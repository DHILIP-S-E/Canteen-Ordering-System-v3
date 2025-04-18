import json
from typing import Dict, Any

class PaymentManager:
    def __init__(self):
        # For demo/test purposes, we'll simulate payment processing
        self.payment_gateway_url = "https://api.payment-gateway.example"
    
    def create_order(self, amount: float, currency: str = "INR") -> Dict[str, Any]:
        """Create a simulated order"""
        try:
            # For demo purposes, always return success
            return {
                'id': f'order_demo_{hash(str(amount))}',  # Simulated order ID
                'amount': amount,
                'currency': currency,
                'status': 'created'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def process_payment(self, amount: float) -> Dict[str, Any]:
        """
        Process a payment (simulated)
        Args:
            amount: Amount to be charged (in INR)
        Returns:
            Dict containing payment details
        """
        try:
            # Create simulated payment
            payment_id = f'pay_{hash(str(amount))}'
            
            return {
                'status': 'success',
                'payment_id': payment_id,
                'amount': amount,
                'message': 'Payment processed successfully'
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
        Verify a payment status (simulated)
        Args:
            payment_id: Payment ID to verify
        Returns:
            Dict containing verification status
        """
        try:
            # For demo purposes, always return success
            return {
                'status': 'success',
                'payment_id': payment_id,
                'message': 'Payment verified successfully'
            }
        except Exception as e:
            return {
                'status': 'error',
                'payment_id': payment_id,
                'message': f'Verification failed: {str(e)}'
            }