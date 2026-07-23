import io
import os

import openpyxl
from django.conf import settings
from django.db.models import Q, Sum
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from kebun.models import Kebun
from petani.models import Petani
from utils.choices import JenisKelamin, JenisLegalitas


def generate_laporan_statistik_kelompok_excel(bulan=None, tahun=None):
    """
    Generate a statistical report of farmer groups in Excel format.
    
    This function creates a comprehensive Excel workbook containing statistics about farmer groups
    including member demographics, document verification, and land legality information. The report
    can be filtered by month and year.
    
    Args:
        bulan (int, optional): Month (1-12) to filter the data. If None or empty string, no month filtering is applied.
        tahun (int, optional): Year to filter the data. If None or empty string, no year filtering is applied.
    
    Returns:
        tuple: A tuple containing:
            - bytes: The Excel file content as bytes.
            - str: Period label string for file naming (e.g., '_01-2024', '_2024', '_bulan1', or '').
    
    The generated Excel report includes:
        - Farmer group statistics (male, female, total members)
        - Document verification counts (ID cards, family cards, permits)
        - Land documentation metrics (plots, hectares)
        - Land legality types (SKT, SHM, TS)
        - Totals and percentages for all metrics
    """
    
    bulan = int(bulan) if bulan not in (None, '') else None
    tahun = int(tahun) if tahun not in (None, '') else None

    period_q = Q()
    if tahun and bulan:
        # Retrieve all historical data up to the target month/year (inclusive).
        period_q = Q(updated_at__year__lt=tahun) | Q(
            updated_at__year=tahun,
            updated_at__month__lte=bulan,
        )
    elif tahun:
        period_q = Q(updated_at__year__lte=tahun)
    elif bulan:
        period_q = Q(updated_at__month__lte=bulan)

    kelompok_list = (
        Petani.objects.filter(period_q)
        .values_list('nama_kelompok', flat=True)
        .distinct()
        .order_by('nama_kelompok')
    )

    all_kebun_qs = Kebun.objects.filter(period_q)
    total_kebun_global = all_kebun_qs.count()
    total_ha_global = round(float(all_kebun_qs.aggregate(t=Sum('luas'))['t'] or 0), 2)

    rows = []
    for kelompok in kelompok_list:
        petani_qs = Petani.objects.filter(period_q, nama_kelompok=kelompok)

        lk = petani_qs.filter(jns_kelamin=JenisKelamin.LAKI_LAKI).count()
        pr = petani_qs.filter(jns_kelamin=JenisKelamin.PEREMPUAN).count()
        total = petani_qs.count()
        ktp = petani_qs.exclude(no_ktp='').exclude(no_ktp__isnull=True).count()
        kk = petani_qs.exclude(no_kk='').exclude(no_kk__isnull=True).count()
        sppl = petani_qs.exclude(tgl_terbit_sppl__isnull=True).count()

        kebun_qs = Kebun.objects.filter(period_q, petani__nama_kelompok=kelompok)

        def _stat(qs):
            qs = qs.distinct()
            plot = qs.count()
            ha = round(float(qs.aggregate(t=Sum('luas'))['t'] or 0), 2)
            return plot, ha

        lahan_plot, lahan_ha = _stat(
            kebun_qs.filter(lampiran__file_legalitas__isnull=False)
            .exclude(lampiran__file_legalitas='')
        )
        peta_plot, peta_ha = _stat(kebun_qs.filter(geom__isnull=False))
        stdb_plot, stdb_ha = _stat(
            kebun_qs.exclude(nomor_stdb='').exclude(nomor_stdb__isnull=True)
        )
        skt_plot, skt_ha = _stat(kebun_qs.filter(jenis_legalitas=JenisLegalitas.SKT))
        shm_plot, shm_ha = _stat(kebun_qs.filter(jenis_legalitas=JenisLegalitas.SHM))
        ts_plot, ts_ha = _stat(
            kebun_qs.filter(nomor_legalitas__isnull=True) | kebun_qs.filter(nomor_legalitas='')
        )

        rows.append(
            {
                'kelompok': kelompok,
                'lk': lk,
                'pr': pr,
                'total': total,
                'ktp': ktp,
                'kk': kk,
                'sppl': sppl,
                'lahan_plot': lahan_plot,
                'lahan_ha': lahan_ha,
                'peta_plot': peta_plot,
                'peta_ha': peta_ha,
                'stdb_plot': stdb_plot,
                'stdb_ha': stdb_ha,
                'skt_plot': skt_plot,
                'skt_ha': skt_ha,
                'shm_plot': shm_plot,
                'shm_ha': shm_ha,
                'ts_plot': ts_plot,
                'ts_ha': ts_ha,
            }
        )

    def _sum(key):
        return sum(r[key] for r in rows)

    gt = {
        k: _sum(k)
        for k in [
            'lk',
            'pr',
            'total',
            'ktp',
            'kk',
            'sppl',
            'lahan_plot',
            'lahan_ha',
            'peta_plot',
            'peta_ha',
            'stdb_plot',
            'stdb_ha',
            'skt_plot',
            'skt_ha',
            'shm_plot',
            'shm_ha',
            'ts_plot',
            'ts_ha',
        ]
    }

    def pct(val, denom):
        if denom == 0:
            return '-'
        return f"{round(val / denom * 100, 2)}%"

    wb = openpyxl.Workbook()
    ws = wb.active
    period_label = ''
    if bulan and tahun:
        period_label = f'_{bulan}-{tahun}'
    elif tahun:
        period_label = f'_{tahun}'
    elif bulan:
        period_label = f'_bulan{bulan}'
    ws.title = 'Laporan Statistik Kelompok'

    bold = Font(bold=True, size=10)
    italic = Font(italic=True, size=10)
    normal = Font(size=10)
    center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left = Alignment(horizontal='left', vertical='center', wrap_text=True)
    thin = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin'),
    )
    fill_h1 = PatternFill(start_color='2F75B6', end_color='2F75B6', fill_type='solid')
    fill_h2 = PatternFill(start_color='BDD7EE', end_color='BDD7EE', fill_type='solid')
    fill_jumlah = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')
    fill_pct = PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid')
    font_h1 = Font(bold=True, size=10, color='FFFFFF')

    col_widths = [4, 26, 5, 5, 7, 6, 6, 6, 7, 10, 7, 10, 7, 10, 7, 10, 7, 10, 7, 10]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    for r in range(1, 7):
        ws.row_dimensions[r].height = 22
    ws.row_dimensions[7].height = 8
    ws.row_dimensions[8].height = 28
    ws.row_dimensions[9].height = 20
    ws.row_dimensions[10].height = 18

    def _hcell(coord, value, fill, font, merge_to=None):
        if merge_to:
            ws.merge_cells(f'{coord}:{merge_to}')
        c = ws[coord]
        c.value = value
        c.font = font
        c.alignment = center
        c.fill = fill
        c.border = thin

    ws.merge_cells('A1:B6')
    ws.merge_cells('C1:T1')
    ws.merge_cells('C2:T2')
    ws.merge_cells('C3:T3')
    ws.merge_cells('C4:T4')
    ws.merge_cells('C5:T5')
    ws.merge_cells('C6:T6')

    kop_org_font = Font(bold=True, size=13)
    kop_text_font = Font(size=10)
    kop_title_font = Font(bold=True, size=11)
    kop_email_font = Font(color='0563C1', underline='single', size=10)
    kop_center = Alignment(horizontal='center', vertical='center', wrap_text=True)

    ws['C1'].value = 'ALIANSI PETANI KELAPA SAWIT KELING KUMANG'
    ws['C1'].font = kop_org_font
    ws['C1'].alignment = kop_center

    ws['C2'].value = 'Alamat : Jalan Sekadau-Sintang, KM 27 Dusun Tapang Sambas, Desa Tapang Sambas'
    ws['C2'].font = kop_text_font
    ws['C2'].alignment = kop_center

    ws['C3'].value = 'Kecamatan Sekadau Hilir, Kabupaten Sekadau, Kalimantan Barat'
    ws['C3'].font = kop_text_font
    ws['C3'].alignment = kop_center

    ws['C4'].value = 'Email : apkskk15@gmail.com'
    ws['C4'].font = kop_email_font
    ws['C4'].alignment = kop_center

    ws['C5'].value = 'Statistik Perkembangan Dokumen & Legalitas Anggota Petani Sertifikasi RSPO'
    ws['C5'].font = kop_title_font
    ws['C5'].alignment = kop_center

    if bulan and tahun:
        kop_period = f"{str(bulan).zfill(2)}/{str(tahun)[-2:]}"
    elif tahun:
        kop_period = str(tahun)
    elif bulan:
        kop_period = f'Bulan {bulan}'
    else:
        kop_period = 'Semua Periode'
    ws['C6'].value = kop_period
    ws['C6'].font = kop_text_font
    ws['C6'].alignment = kop_center

    for col_idx in range(1, 21):
        ws.cell(row=7, column=col_idx).border = Border(top=Side(style='medium'))

    logo_path = os.path.join(settings.BASE_DIR, 'assets', 'logo.png')
    if os.path.exists(logo_path):
        from openpyxl.drawing.image import Image as XLImage

        img = XLImage(logo_path)
        img.width = 140
        img.height = 115
        ws.add_image(img, 'A1')

    _hcell('A8', 'No', fill_h1, font_h1, 'A10')
    _hcell('B8', 'Nama Kelompok', fill_h1, font_h1, 'B10')
    _hcell('C8', 'Jumlah Anggota', fill_h1, font_h1, 'E8')
    _hcell('F8', 'Dokumen Anggota', fill_h1, font_h1, 'H8')
    _hcell('I8', 'Dokumen Kebun Petani', fill_h1, font_h1, 'T8')

    _hcell('C9', 'LK', fill_h2, bold, 'C10')
    _hcell('D9', 'PR', fill_h2, bold, 'D10')
    _hcell('E9', 'Total', fill_h2, bold, 'E10')
    _hcell('F9', 'KTP', fill_h2, bold, 'F10')
    _hcell('G9', 'KK', fill_h2, bold, 'G10')
    _hcell('H9', 'SPPL', fill_h2, bold, 'H10')
    _hcell('I9', 'LAHAN', fill_h2, bold, 'J9')
    _hcell('K9', 'Peta', fill_h2, bold, 'L9')
    _hcell('M9', 'STD-B', fill_h2, bold, 'N9')
    _hcell('O9', 'SKT', fill_h2, bold, 'P9')
    _hcell('Q9', 'SHM', fill_h2, bold, 'R9')
    _hcell('S9', 'TS', fill_h2, bold, 'T9')

    for col in ['I', 'K', 'M', 'O', 'Q', 'S']:
        idx = ord(col) - ord('A') + 1
        next_col = get_column_letter(idx + 1)
        _hcell(f'{col}10', 'Plot', fill_h2, bold)
        _hcell(f'{next_col}10', 'Ha', fill_h2, bold)

    ws.freeze_panes = 'A11'

    def _row(row_num, values, fill=None, fnt=None):
        for col, val in enumerate(values, 1):
            c = ws.cell(row=row_num, column=col, value=val)
            c.border = thin
            c.font = fnt or normal
            c.alignment = left if col == 2 else center
            if fill:
                c.fill = fill

    _row(
        11,
        [
            'A',
            'JUMLAH',
            gt['lk'],
            gt['pr'],
            gt['total'],
            gt['ktp'],
            gt['kk'],
            gt['sppl'],
            gt['lahan_plot'],
            gt['lahan_ha'],
            gt['peta_plot'],
            gt['peta_ha'],
            gt['stdb_plot'],
            gt['stdb_ha'],
            gt['skt_plot'],
            gt['skt_ha'],
            gt['shm_plot'],
            gt['shm_ha'],
            gt['ts_plot'],
            gt['ts_ha'],
        ],
        fill=fill_jumlah,
        fnt=bold,
    )

    ta = gt['total']
    _row(
        12,
        [
            'B',
            'Presentase',
            pct(gt['lk'], ta),
            pct(gt['pr'], ta),
            '100%',
            pct(gt['ktp'], ta),
            pct(gt['kk'], ta),
            pct(gt['sppl'], ta),
            pct(gt['lahan_plot'], total_kebun_global),
            pct(gt['lahan_ha'], total_ha_global),
            pct(gt['peta_plot'], total_kebun_global),
            pct(gt['peta_ha'], total_ha_global),
            pct(gt['stdb_plot'], total_kebun_global),
            pct(gt['stdb_ha'], total_ha_global),
            pct(gt['skt_plot'], total_kebun_global),
            pct(gt['skt_ha'], total_ha_global),
            pct(gt['shm_plot'], total_kebun_global),
            pct(gt['shm_ha'], total_ha_global),
            pct(gt['ts_plot'], total_kebun_global),
            pct(gt['ts_ha'], total_ha_global),
        ],
        fill=fill_pct,
        fnt=italic,
    )

    for idx, r in enumerate(rows, 1):
        _row(
            12 + idx,
            [
                idx,
                r['kelompok'],
                r['lk'],
                r['pr'],
                r['total'],
                r['ktp'],
                r['kk'],
                r['sppl'],
                r['lahan_plot'],
                r['lahan_ha'],
                r['peta_plot'],
                r['peta_ha'],
                r['stdb_plot'],
                r['stdb_ha'],
                r['skt_plot'],
                r['skt_ha'],
                r['shm_plot'],
                r['shm_ha'],
                r['ts_plot'],
                r['ts_ha'],
            ],
        )

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue(), period_label
