from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Petani, Lampiran


class LampiranPetaniTestCase(TestCase):
    """Test cases for the Lampiran Petani model"""
    
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
    
    def create_dummy_file(self, size_in_mb, filename='test.pdf'):
        """Helper to create a dummy file with a specific size"""
        size_in_bytes = size_in_mb * 1024 * 1024
        content = b'0' * int(size_in_bytes)
        return SimpleUploadedFile(filename, content, content_type='application/pdf')
    
    def create_dummy_image(self, size_in_mb, filename='test.jpg'):
        """Helper to create a dummy image file"""
        size_in_bytes = size_in_mb * 1024 * 1024
        content = b'0' * int(size_in_bytes)
        return SimpleUploadedFile(filename, content, content_type='image/jpeg')
    
    def test_create_lampiran_petani(self):
        """Test creating a farmer attachment without files"""
        lampiran = Lampiran.objects.create(petani=self.petani)
        
        self.assertIsNotNone(lampiran)
        self.assertEqual(lampiran.petani, self.petani)
        self.assertFalse(lampiran.file_ktp)
        self.assertFalse(lampiran.file_kk)
        self.assertFalse(lampiran.file_nib)
    
    def test_upload_file_valid_size(self):
        """Test uploading a file with a valid size (< 10MB)"""
        # Create a 5MB file
        file_5mb = self.create_dummy_file(5, 'ktp.pdf')
        
        lampiran = Lampiran.objects.create(
            petani=self.petani,
            file_ktp=file_5mb
        )
        
        self.assertTrue(lampiran.file_ktp)
        self.assertIn('ktp', lampiran.file_ktp.name)
    
    def test_upload_file_exceed_limit(self):
        """Test uploading a file that exceeds the 10MB limit"""
        # Create a 11MB file
        file_11mb = self.create_dummy_file(11, 'large_ktp.pdf')
        
        lampiran = Lampiran(
            petani=self.petani,
            file_ktp=file_11mb
        )
        
        # Validation should fail
        with self.assertRaises(ValidationError) as context:
            lampiran.full_clean()
        
        self.assertIn('file_ktp', context.exception.message_dict)
        self.assertIn('10 MB', str(context.exception))
    
    def test_upload_file_kk_exceed_limit(self):
        """Test uploading a KK file that exceeds the 10MB limit"""
        # Create a 12MB file
        file_12mb = self.create_dummy_file(12, 'large_kk.pdf')
        
        lampiran = Lampiran(
            petani=self.petani,
            file_kk=file_12mb
        )
        
        # Validation should fail
        with self.assertRaises(ValidationError) as context:
            lampiran.full_clean()
        
        self.assertIn('file_kk', context.exception.message_dict)
    
    def test_upload_file_nib_exceed_limit(self):
        """Test uploading a NIB file that exceeds the 10MB limit"""
        # Create a 15MB file
        file_15mb = self.create_dummy_file(15, 'large_nib.pdf')
        
        lampiran = Lampiran(
            petani=self.petani,
            file_nib=file_15mb
        )
        
        # Validation should fail
        with self.assertRaises(ValidationError) as context:
            lampiran.full_clean()
        
        self.assertIn('file_nib', context.exception.message_dict)
    
    def test_upload_file_at_limit(self):
        """Test uploading a file exactly at the limit (10MB)"""
        # Create a file exactly 10MB
        file_10mb = self.create_dummy_file(10, 'limit_kk.pdf')
        
        lampiran = Lampiran(
            petani=self.petani,
            file_kk=file_10mb
        )
        
        # Validation should succeed
        try:
            lampiran.full_clean()
            lampiran.save()
            self.assertTrue(lampiran.file_kk)
        except ValidationError:
            self.fail("A 10MB file should be valid")
    
    def test_upload_multiple_files(self):
        """Test uploading multiple files at once"""
        file_ktp = self.create_dummy_file(2, 'ktp.pdf')
        file_kk = self.create_dummy_file(3, 'kk.pdf')
        file_nib = self.create_dummy_file(1, 'nib.pdf')
        
        lampiran = Lampiran.objects.create(
            petani=self.petani,
            file_ktp=file_ktp,
            file_kk=file_kk,
            file_nib=file_nib
        )
        
        self.assertTrue(lampiran.file_ktp)
        self.assertTrue(lampiran.file_kk)
        self.assertTrue(lampiran.file_nib)
    
    def test_one_to_one_relationship(self):
        """Test the OneToOne relationship with Petani"""
        from django.db import transaction
        
        lampiran1 = Lampiran.objects.create(petani=self.petani)
        
        # Attempt to create a second attachment for the same farmer (should fail)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Lampiran.objects.create(petani=self.petani)
    
    def test_update_file(self):
        """Test updating an existing file"""
        file_old = self.create_dummy_file(1, 'old_ktp.pdf')
        lampiran = Lampiran.objects.create(
            petani=self.petani,
            file_ktp=file_old
        )
        
        old_filename = lampiran.file_ktp.name
        
        # Update with a new file
        file_new = self.create_dummy_file(2, 'new_ktp.pdf')
        lampiran.file_ktp = file_new
        lampiran.save()
        
        self.assertNotEqual(lampiran.file_ktp.name, old_filename)
        self.assertIn('new_ktp', lampiran.file_ktp.name)
    
    def test_delete_lampiran_cascade(self):
        """Test deleting the attachment when the farmer is deleted (cascade)"""
        lampiran = Lampiran.objects.create(petani=self.petani)
        lampiran_id = lampiran.id
        
        # Delete the farmer
        self.petani.delete()
        
        # The attachment should also be deleted
        with self.assertRaises(Lampiran.DoesNotExist):
            Lampiran.objects.get(id=lampiran_id)
    
    def test_delete_lampiran_only(self):
        """Test deleting only the attachment (the farmer remains)"""
        lampiran = Lampiran.objects.create(petani=self.petani)
        lampiran_id = lampiran.id
        
        lampiran.delete()
        
        # Delete the attachment
        with self.assertRaises(Lampiran.DoesNotExist):
            Lampiran.objects.get(id=lampiran_id)
        
        # The farmer still exists
        self.assertTrue(Petani.objects.filter(id=self.petani.id).exists())
    
    def test_string_representation(self):
        """Test the __str__ method"""
        lampiran = Lampiran.objects.create(petani=self.petani)
        expected_str = f"lampiran: {self.petani}"
        
        self.assertEqual(str(lampiran), expected_str)
    
    def test_mapping_field_names(self):
        """Test the _get_mapping_field_names method for thumbnails"""
        lampiran = Lampiran.objects.create(petani=self.petani)
        mapping = lampiran._get_mapping_field_names()
        
        self.assertIn('file_ktp', mapping)
        self.assertEqual(mapping['file_ktp'], 'thumb_ktp')
        self.assertIn('file_kk', mapping)
        self.assertEqual(mapping['file_kk'], 'thumb_kk')
        self.assertIn('file_nib', mapping)
        self.assertEqual(mapping['file_nib'], 'thumb_nib')
    
    def test_upload_with_partial_files(self):
        """Test uploading only some files"""
        file_ktp = self.create_dummy_file(2, 'ktp.pdf')
        
        lampiran = Lampiran.objects.create(
            petani=self.petani,
            file_ktp=file_ktp
            # file_kk and file_nib are not provided
        )
        
        self.assertTrue(lampiran.file_ktp)
        self.assertFalse(lampiran.file_kk)
        self.assertFalse(lampiran.file_nib)
    
    def tearDown(self):
        """Clean up after each test"""
        # Clean up uploaded files
        Lampiran.objects.all().delete()
        Petani.objects.all().delete()


class PetaniModelTestCase(TestCase):
    """Additional test cases for the Petani model"""
    
    def test_create_petani(self):
        """Test creating a new farmer"""
        petani = Petani.objects.create(
            id_petani='TEST002',
            nama='Budi Santoso',
            nama_kelompok='Kelompok Makmur',
            jns_kelamin='L',
            no_ktp='9876543210123456'
        )
        
        self.assertIsNotNone(petani)
        self.assertEqual(petani.nama, 'Budi Santoso')
    
    def test_petani_string_representation(self):
        """Test the Petani __str__ method"""
        petani = Petani.objects.create(
            id_petani='TEST003',
            nama='Siti Aminah',
            nama_kelompok='Kelompok Maju',
            jns_kelamin='P',
            no_ktp='1122334455667788'
        )
        
        self.assertEqual(str(petani), 'Siti Aminah')


class LampiranPetaniAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tester_petani',
            password='secret123',
            roles=['1'],
        )
        self.client.force_authenticate(user=self.user)

        self.petani = Petani.objects.create(
            id_petani='PETANI_API_002',
            nama='Petani API 2',
            nama_kelompok='Kelompok API 2',
            jns_kelamin='L',
            no_ktp='9876543210123456',
        )

    def _pdf_file(self, name='dokumen.pdf'):
        return SimpleUploadedFile(name, b'%PDF-1.4 test content', content_type='application/pdf')

    def test_create_lampiran_returns_output_serializer_payload(self):
        response = self.client.post(
            '/petani/lampiran/create/',
            {
                'petani_id': self.petani.id,
                'file_ktp': self._pdf_file('ktp_api.pdf'),
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('file_ktp', response.data['data'])
        self.assertIn('thumb_ktp', response.data['data'])
        self.assertTrue(response.data['data']['file_ktp'].startswith('http'))

    def test_update_lampiran_returns_output_serializer_payload(self):
        Lampiran.objects.create(petani=self.petani)

        response = self.client.put(
            f'/petani/lampiran/update/{self.petani.id}/',
            {
                'file_kk': self._pdf_file('kk_api.pdf'),
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('file_kk', response.data['data'])
        self.assertIn('thumb_kk', response.data['data'])
        self.assertTrue(response.data['data']['file_kk'].startswith('http'))
