from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.gis.geos import Point
from django.contrib.auth import get_user_model
from decimal import Decimal
from io import BytesIO
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Kebun, Lampiran
from petani.models import Petani


class LampiranKebunTestCase(TestCase):
    """Test cases for the Lampiran Kebun model"""
    
    def setUp(self):
        """Set up test data"""
        # Create a farmer
        self.petani = Petani.objects.create(
            id_petani='TEST001',
            nama='Petani Test',
            nama_kelompok='Kelompok Test',
            jns_kelamin='L',
            no_ktp='1234567890123456'
        )
        
        # Create a kebun
        self.kebun = Kebun.objects.create(
            id_kebun='KBN001',
            petani=self.petani,
            lokasi_kebun='Test Location',
            luas=Decimal('10.5'),
            jumlah_pokok=100,
            titik_koordinat=Point(106.8456, -6.2088)
        )
    
    def create_dummy_file(self, size_in_mb, filename='test.pdf'):
        """Helper to create a dummy file with a specific size"""
        size_in_bytes = size_in_mb * 1024 * 1024
        content = b'0' * int(size_in_bytes)
        return SimpleUploadedFile(filename, content, content_type='application/pdf')
    
    def test_create_lampiran_kebun(self):
        """Test creating a kebun attachment without files"""
        lampiran = Lampiran.objects.create(kebun=self.kebun)
        
        self.assertIsNotNone(lampiran)
        self.assertEqual(lampiran.kebun, self.kebun)
        self.assertFalse(lampiran.file_legalitas)
        self.assertFalse(lampiran.file_stdb)
    
    def test_upload_file_valid_size(self):
        """Test uploading a file with a valid size (< 10MB)"""
        # Create a 5MB file
        file_5mb = self.create_dummy_file(5, 'legalitas.pdf')
        
        lampiran = Lampiran.objects.create(
            kebun=self.kebun,
            file_legalitas=file_5mb
        )
        
        self.assertTrue(lampiran.file_legalitas)
        self.assertIn('legalitas', lampiran.file_legalitas.name)
    
    def test_upload_file_exceed_limit(self):
        """Test uploading a file that exceeds the 10MB limit"""
        # Create a 11MB file
        file_11mb = self.create_dummy_file(11, 'large_file.pdf')
        
        lampiran = Lampiran(
            kebun=self.kebun,
            file_legalitas=file_11mb
        )
        
        # Validation should fail
        with self.assertRaises(ValidationError) as context:
            lampiran.full_clean()
        
        self.assertIn('file_legalitas', context.exception.message_dict)
        self.assertIn('10 MB', str(context.exception))
    
    def test_upload_file_at_limit(self):
        """Test uploading a file exactly at the limit (10MB)"""
        # Create a file exactly 10MB
        file_10mb = self.create_dummy_file(10, 'limit_file.pdf')
        
        lampiran = Lampiran(
            kebun=self.kebun,
            file_stdb=file_10mb
        )
        
        # Validation should succeed
        try:
            lampiran.full_clean()
            lampiran.save()
            self.assertTrue(lampiran.file_stdb)
        except ValidationError:
            self.fail("A 10MB file should be valid")
    
    def test_upload_multiple_files(self):
        """Test uploading multiple files at once"""
        file_legalitas = self.create_dummy_file(2, 'legalitas.pdf')
        file_stdb = self.create_dummy_file(3, 'stdb.pdf')
        file_rspo = self.create_dummy_file(1, 'rspo.pdf')
        file_ispo = self.create_dummy_file(2, 'ispo.pdf')
        
        lampiran = Lampiran.objects.create(
            kebun=self.kebun,
            file_legalitas=file_legalitas,
            file_stdb=file_stdb,
            file_rspo=file_rspo,
            file_ispo=file_ispo
        )
        
        self.assertTrue(lampiran.file_legalitas)
        self.assertTrue(lampiran.file_stdb)
        self.assertTrue(lampiran.file_rspo)
        self.assertTrue(lampiran.file_ispo)
    
    def test_one_to_one_relationship(self):
        """Test the OneToOne relationship with Kebun"""
        from django.db import transaction
        
        lampiran1 = Lampiran.objects.create(kebun=self.kebun)
        
        # Attempt to create a second attachment for the same kebun (should fail)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Lampiran.objects.create(kebun=self.kebun)
    
    def test_update_file(self):
        """Test updating an existing file"""
        file_old = self.create_dummy_file(1, 'old.pdf')
        lampiran = Lampiran.objects.create(
            kebun=self.kebun,
            file_legalitas=file_old
        )
        
        old_filename = lampiran.file_legalitas.name
        
        # Update with a new file
        file_new = self.create_dummy_file(2, 'new.pdf')
        lampiran.file_legalitas = file_new
        lampiran.save()
        
        self.assertNotEqual(lampiran.file_legalitas.name, old_filename)
        self.assertIn('new', lampiran.file_legalitas.name)
    
    def test_delete_lampiran(self):
        """Test deleting the attachment"""
        lampiran = Lampiran.objects.create(kebun=self.kebun)
        lampiran_id = lampiran.id
        
        lampiran.delete()
        
        with self.assertRaises(Lampiran.DoesNotExist):
            Lampiran.objects.get(id=lampiran_id)
    
    def test_mapping_field_names(self):
        """Test the _get_mapping_field_names method for thumbnails"""
        lampiran = Lampiran.objects.create(kebun=self.kebun)
        mapping = lampiran._get_mapping_field_names()
        
        self.assertIn('file_legalitas', mapping)
        self.assertEqual(mapping['file_legalitas'], 'thumb_legalitas')
        self.assertIn('file_stdb', mapping)
        self.assertEqual(mapping['file_stdb'], 'thumb_stdb')
        self.assertIn('file_rspo', mapping)
        self.assertEqual(mapping['file_rspo'], 'thumb_rspo')
        self.assertIn('file_ispo', mapping)
        self.assertEqual(mapping['file_ispo'], 'thumb_ispo')
    
    def tearDown(self):
        """Clean up after each test"""
        # Clean up uploaded files
        Lampiran.objects.all().delete()
        Kebun.objects.all().delete()
        Petani.objects.all().delete()


class LampiranKebunAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tester_kebun',
            password='secret123',
            roles=['1'],
        )
        self.client.force_authenticate(user=self.user)

        self.petani = Petani.objects.create(
            id_petani='PETANI_API_001',
            nama='Petani API',
            nama_kelompok='Kelompok API',
            jns_kelamin='L',
            no_ktp='1234567890123456',
        )

        self.kebun = Kebun.objects.create(
            id_kebun='KBN_API_001',
            petani=self.petani,
            lokasi_kebun='Lokasi API',
            luas=Decimal('5.00'),
            jumlah_pokok=50,
            titik_koordinat=Point(106.8456, -6.2088),
        )

    def _pdf_file(self, name='dokumen.pdf'):
        return SimpleUploadedFile(name, b'%PDF-1.4 test content', content_type='application/pdf')

    def test_create_lampiran_returns_output_serializer_payload(self):
        response = self.client.post(
            '/kebun/lampiran/create/',
            {
                'kebun_id': self.kebun.id,
                'file_legalitas': self._pdf_file('legalitas_api.pdf'),
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('file_legalitas', response.data['data'])
        self.assertIn('thumb_legalitas', response.data['data'])
        self.assertTrue(response.data['data']['file_legalitas'].startswith('http'))

    def test_update_lampiran_returns_output_serializer_payload(self):
        Lampiran.objects.create(kebun=self.kebun)

        response = self.client.put(
            f'/kebun/lampiran/update/{self.kebun.id}/',
            {
                'file_stdb': self._pdf_file('stdb_api.pdf'),
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('file_stdb', response.data['data'])
        self.assertIn('thumb_stdb', response.data['data'])
        self.assertTrue(response.data['data']['file_stdb'].startswith('http'))
