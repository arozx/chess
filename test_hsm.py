import unittest
from hsm import HSM

class TestHSM(unittest.TestCase):
    def setUp(self):
        self.key = "0123456789abcdef"
        self.iv = "fedcba9876543210"
        self.hsm = HSM(self.key, self.iv)

    """
    def test_encrypt_decrypt(self):
        plaintext = "Hello, World!"
        encrypted = self.hsm.encrypt(plaintext)
        decrypted = self.hsm.decrypt(encrypted)
        self.assertEqual(decrypted, plaintext)
    """

    def test_generate_random_key(self):
        random_key = self.hsm.generate_random_key()
        self.assertEqual(len(random_key), 16)
