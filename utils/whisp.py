import requests
import logging
import json
from django.utils import timezone
from kebun.models import Kebun, KebunDeforestationAnalysis
from django.conf import settings
from django.utils import timezone
from typing import Dict, Any
from utils.choices import WHISPStatus


logger = logging.getLogger(__name__)


class WHISPService:
    """
    Service class for interacting with the WHISP API.
    
    This service handles geometry analysis for deforestation detection by communicating
    with the WHISP (Woodland-Health-Information-System-Platform) API. It manages the 
    submission of geographic data and tracks analysis status through the database.
    
    Attributes:
        base_url (str): The base URL of the WHISP API from Django settings.
        api_key (str): The API key for authentication with the WHISP API from Django settings.
    """
    def __init__(self):
        self.base_url = settings.WHISP_API_URL
        self.api_key = settings.WHISP_API_KEY

    def check_geometry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send geometry to WHISP API for analysis
        """
        try:
            headers = {
                'X-API-KEY': str(self.api_key),
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'{self.base_url}/submit/geojson',
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return {
                    'status': 'success',
                    'data': response.json(),
                    'timestamp': timezone.now().isoformat()
                }
            else:
                logger.error(f"WHISP API error: {response.status_code} - {response.text}")
                return {
                    'status': 'error',
                    'error': f'API returned status {response.status_code}',
                    'timestamp': timezone.now().isoformat()
                }
                
        except requests.exceptions.Timeout:
            logger.error("WHISP API timeout")
            return {
                'status': 'error',
                'error': 'Request timeout',
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"WHISP API error: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }

    def process_whisp_analysis(self, kebun_id: int):
        """
        Job to analyze farm geometry with WHISP package
        """
        try:
            kebun = Kebun.objects.filter(id=kebun_id).first()
            deforestation_analysis, _ = KebunDeforestationAnalysis.objects.get_or_create(kebun=kebun)
            
            if not kebun.geom:
                logger.warning(f"Kebun {kebun_id} tidak memiliki geometri, tidak dapat melakukan analisis WHISP")
                deforestation_analysis.whisp_status = WHISPStatus.ERROR
                deforestation_analysis.whisp_analysis = {
                    'status': WHISPStatus.ERROR,
                    'error': 'No geometry found',
                    'timestamp': timezone.now().isoformat()
                }
                deforestation_analysis.save()
                return {'status': WHISPStatus.ERROR, 'message': 'Tidak ada geometri yang ditemukan'}
            
            # Update status to processing
            deforestation_analysis.whisp_status = WHISPStatus.PROCESSING
            deforestation_analysis.save()

            logger.info(f"Starting WHISP analysis for kebun {kebun_id}")
            
            # Call WHISP service
            payload = json.loads(kebun.geom.geojson)
            result = self.check_geometry(payload)

            # Update kebun with analysis results
            status = WHISPStatus.COMPLETED if result['status'] == 'success' else WHISPStatus.ERROR
            deforestation_analysis.whisp_analysis = result
            deforestation_analysis.whisp_status = status
            deforestation_analysis.whisp_job_id = None  # Clear job ID after completion
            deforestation_analysis.save()

            logger.info(f"WHISP analysis completed for kebun {kebun_id}: {result['status']}")
            return {'status': status, 'kebun_id': kebun_id, 'result': result['status']}
            
        except Kebun.DoesNotExist:
            logger.error(f"Kebun {kebun_id} not found")
            return {'status': 'error', 'message': 'Kebun not found'}
        except Exception as e:
            logger.error(f"Error in WHISP analysis for kebun {kebun_id}: {str(e)}")
            
            # Update status to error
            try:
                kebun = Kebun.objects.get(id=kebun_id)
                deforestation_analysis, _ = KebunDeforestationAnalysis.objects.get_or_create(kebun=kebun)
                deforestation_analysis.whisp_status = 'error'
                deforestation_analysis.whisp_analysis = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': timezone.now().isoformat()
                }
                deforestation_analysis.whisp_job_id = None
                deforestation_analysis.save(update_fields=['whisp_status', 'whisp_analysis', 'whisp_job_id'])
            except Exception as save_error:
                logger.error(f"Failed to update kebun status after error: {save_error}")
            
            return {'status': 'error', 'message': str(e)}