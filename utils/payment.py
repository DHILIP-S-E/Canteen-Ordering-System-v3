import razorpay
import json
from typing import Dict, Any

class PaymentManager:
    def __init__(self):
        # Initialize with test credentials - replace with real ones in production
        self.client = razorpay.Client(
            auth=("rzp_test_your_key", "your_secret_key")
        )
    
    def create_order(self, amount, currency="INR"):
        """Create a Razorpay order"""
        try:
            # For demo purposes, always return success
            return {
                'id': 'order_demo123',
                'amount': amount,
                'currency': currency,
                'status': 'created'
            }
        except Exception as e:
            return None
    
    def process_payment(self, amount: float) -> Dict[str, Any]:
        """
        Process a payment through Razorpay
        Args:
            amount: Amount to be charged (in INR)
        Returns:
            Dict containing payment details
        """
        try:
            # Convert amount to paise (Razorpay expects amount in smallest currency unit)
            amount_in_paise = int(amount * 100)
            
            # Create Razorpay order
            payment_data = {
                'amount': amount_in_paise,
                'currency': 'INR',
                'payment_capture': '1'
            }
            
            order = self.client.order.create(data=payment_data)
            
            return {
                'status': 'success',
                'payment_id': order['id'],
                'amount': amount,
                'message': 'Payment initiated successfully'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'payment_id': None,
                'amount': amount,
                'message': f'Payment failed: {str(e)}'
            }
    
    def verify_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Verify a payment status with Razorpay
        Args:
            payment_id: Razorpay payment ID
        Returns:
            Dict containing verification status
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            if payment['status'] == 'captured':
                return {
                    'status': 'success',
                    'payment_id': payment_id,
                    'message': 'Payment verified successfully'
                }
            return {
                'status': 'pending',
                'payment_id': payment_id,
                'message': f'Payment status: {payment["status"]}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'payment_id': payment_id,
                'message': f'Verification failed: {str(e)}'
            }