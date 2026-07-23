from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from utils.choices import (
    JenisKelamin, UserRole, RegisteredVia, PendidikanTerakhir, JenisLegalitas, StatusPerkawinan,
    SumberKontak, RequestOTPVia, PenerimaBoardcast, StatusPekerja, WHISPStatus, PilihanBulan, DeforestationSourceType,
    StatusKeanggotaan, StatusLahan, PolaTanam, AsalBenih, JenisLahan, JenisPupuk, JenisPekerjaan, JenisAPD, KomoditasKelembagaan,
    StatusSTDB
)
from utils.serializers import custom_response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


REF_CACHE_TIMEOUT = 60 * 60  # 1 hour


class ReferenceView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    choice_class = None
    
    @method_decorator(cache_page(REF_CACHE_TIMEOUT))
    def get(self, request):
        data = [
            {"value": choice.value, "label": choice.label}
            for choice in self.choice_class
        ]
        return Response(custom_response("success", "Successfully fetched data", data),
                        status=status.HTTP_200_OK)
        

class JenisKelaminView(ReferenceView):
    choice_class = JenisKelamin


class UserRoleView(ReferenceView):
    choice_class = UserRole


class RegisteredViaView(ReferenceView):
    choice_class = RegisteredVia


class PendidikanTerakhirView(ReferenceView):
    choice_class = PendidikanTerakhir
    

class JenisLegalitasView(ReferenceView):
    choice_class = JenisLegalitas


class StatusPerkawinanView(ReferenceView):
    choice_class = StatusPerkawinan


class SumberKontakView(ReferenceView):
    choice_class = SumberKontak


class RequestOTPViaView(ReferenceView):
    choice_class = RequestOTPVia


class PenerimaBoardcastView(ReferenceView):
    choice_class = PenerimaBoardcast


class StatusPekerjaView(ReferenceView):
    choice_class = StatusPekerja


class WHISPStatusView(ReferenceView):
    choice_class = WHISPStatus


class PilihanBulanView(ReferenceView):
    choice_class = PilihanBulan


class DeforestationSourceTypeView(ReferenceView):
    choice_class = DeforestationSourceType


class StatusKeanggotaanView(ReferenceView):
    choice_class = StatusKeanggotaan


class StatusLahanView(ReferenceView):
    choice_class = StatusLahan


class PolaTanamView(ReferenceView):
    choice_class = PolaTanam


class AsalBenihView(ReferenceView):
    choice_class = AsalBenih


class JenisLahanView(ReferenceView):
    choice_class = JenisLahan


class JenisPupukView(ReferenceView):
    choice_class = JenisPupuk


class JenisPekerjaanView(ReferenceView):
    choice_class = JenisPekerjaan


class JenisAPDView(ReferenceView):
    choice_class = JenisAPD


class KomoditasKelembagaanView(ReferenceView):
    choice_class = KomoditasKelembagaan


class StatusSTDBView(ReferenceView):
    choice_class = StatusSTDB
