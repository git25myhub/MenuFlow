from datetime import datetime, timedelta
from sqlalchemy import func, and_
from models import db, Order, CommissionConfig, CommissionTransaction, CommissionBill, User, PlatformSettings
import logging

logger = logging.getLogger(__name__)

class CommissionService:
    """Service class for handling commission calculations and operations"""
    
    @staticmethod
    def calculate_order_commission(order_id):
        """Calculate and store commission for a specific order"""
        try:
            order = Order.query.get(order_id)
            if not order:
                logger.error(f"Order {order_id} not found")
                return None
                
            commission_amount = order.calculate_commission()
            
            # Create commission transaction
            transaction = CommissionTransaction(
                order_id=order.id,
                restaurant_id=order.restaurant_id,
                order_amount=order.total_amount,
                commission_amount=commission_amount,
                commission_rate_used=order.get_commission_rate(),
                commission_type=order.get_commission_type(),
                status='pending'
            )
            
            # Update order
            order.commission_amount = commission_amount
            order.commission_status = 'calculated'
            
            db.session.add(transaction)
            db.session.commit()
            
            logger.info(f"Commission calculated for order {order_id}: {commission_amount} KES")
            return transaction
            
        except Exception as e:
            logger.error(f"Error calculating commission for order {order_id}: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def process_payment_commission(order_id):
        """Process commission when order is paid"""
        try:
            order = Order.query.get(order_id)
            if not order or order.status != 'paid':
                return False
                
            transaction = CommissionTransaction.query.filter_by(order_id=order.id).first()
            if transaction:
                transaction.status = 'paid'
                transaction.payment_date = datetime.utcnow()
                order.commission_status = 'paid'
                db.session.commit()
                
                logger.info(f"Commission payment processed for order {order_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error processing commission payment for order {order_id}: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_restaurant_commission_summary(restaurant_id, start_date=None, end_date=None):
        """Get commission summary for a restaurant"""
        try:
            query = CommissionTransaction.query.filter_by(restaurant_id=restaurant_id)
            
            if start_date:
                query = query.filter(CommissionTransaction.created_at >= start_date)
            if end_date:
                query = query.filter(CommissionTransaction.created_at <= end_date)
                
            transactions = query.all()
            
            total_orders = len(transactions)
            total_commission = sum(t.commission_amount for t in transactions)
            pending_commission = sum(t.commission_amount for t in transactions if t.status == 'pending')
            paid_commission = sum(t.commission_amount for t in transactions if t.status == 'paid')
            
            return {
                'total_orders': total_orders,
                'total_commission': round(total_commission, 2),
                'pending_commission': round(pending_commission, 2),
                'paid_commission': round(paid_commission, 2),
                'average_commission_per_order': round(total_commission / total_orders, 2) if total_orders > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting commission summary for restaurant {restaurant_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_platform_commission_summary(start_date=None, end_date=None):
        """Get overall platform commission summary"""
        try:
            query = CommissionTransaction.query
            
            if start_date:
                query = query.filter(CommissionTransaction.created_at >= start_date)
            if end_date:
                query = query.filter(CommissionTransaction.created_at <= end_date)
                
            transactions = query.all()
            
            total_commission = sum(t.commission_amount for t in transactions)
            pending_commission = sum(t.commission_amount for t in transactions if t.status == 'pending')
            paid_commission = sum(t.commission_amount for t in transactions if t.status == 'paid')
            
            # Group by restaurant
            restaurant_commissions = {}
            for t in transactions:
                if t.restaurant_id not in restaurant_commissions:
                    restaurant_commissions[t.restaurant_id] = 0
                restaurant_commissions[t.restaurant_id] += t.commission_amount
            
            return {
                'total_commission': round(total_commission, 2),
                'pending_commission': round(pending_commission, 2),
                'paid_commission': round(paid_commission, 2),
                'restaurant_count': len(restaurant_commissions),
                'average_commission_per_restaurant': round(total_commission / len(restaurant_commissions), 2) if restaurant_commissions else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting platform commission summary: {str(e)}")
            return None
    
    @staticmethod
    def generate_monthly_commission_bill(restaurant_id, year, month):
        """Generate monthly commission bill for a restaurant"""
        try:
            # Calculate period (inclusive of the last day up to 23:59:59)
            period_start = datetime(year, month, 1)
            if month == 12:
                period_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
            else:
                period_end = datetime(year, month + 1, 1) - timedelta(seconds=1)
            
            # Get commission transactions for the period
            transactions = CommissionTransaction.query.filter(
                and_(
                    CommissionTransaction.restaurant_id == restaurant_id,
                    CommissionTransaction.created_at >= period_start,
                    CommissionTransaction.created_at <= period_end
                )
            ).all()
            
            if not transactions:
                return None
            
            total_commission = sum(t.commission_amount for t in transactions)
            orders_count = len(transactions)
            
            # Set due date (15th of next month)
            if month == 12:
                due_date = datetime(year + 1, 1, 15)
            else:
                due_date = datetime(year, month + 1, 15)
            
            # Create commission bill
            bill = CommissionBill(
                restaurant_id=restaurant_id,
                period_start=period_start,
                period_end=period_end,
                total_commission=total_commission,
                orders_count=orders_count,
                status='pending',
                due_date=due_date
            )
            
            db.session.add(bill)
            db.session.commit()
            
            logger.info(f"Generated commission bill for restaurant {restaurant_id}, period {year}-{month}")
            return bill
            
        except Exception as e:
            logger.error(f"Error generating commission bill for restaurant {restaurant_id}: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def confirm_commission_payment(bill_id, payment_reference, amount_received, confirmer_user_id=None):
        """Confirm commission payment received. Supports partial payments."""
        try:
            bill = CommissionBill.query.get(bill_id)
            if not bill:
                return False, "Bill not found"
            
            # Accumulate amount received
            new_total_received = (bill.amount_received or 0.0) + float(amount_received or 0.0)
            bill.amount_received = round(new_total_received, 2)
            bill.payment_reference = payment_reference
            if confirmer_user_id:
                bill.confirmed_by_user_id = confirmer_user_id
            
            # Determine bill status
            tolerance = 1.0
            if bill.amount_received + tolerance < bill.total_commission:
                bill.status = 'partially_paid'
            else:
                bill.status = 'paid'
                bill.paid_date = datetime.utcnow()
            
            # Update all related commission transactions
            transactions = CommissionTransaction.query.filter(
                and_(
                    CommissionTransaction.restaurant_id == bill.restaurant_id,
                    CommissionTransaction.created_at >= bill.period_start,
                    CommissionTransaction.created_at <= bill.period_end
                )
            ).all()
            
            # If fully paid mark all as paid; if partial, proportionally mark oldest first
            if bill.status == 'paid':
                for transaction in transactions:
                    transaction.status = 'paid'
                    transaction.payment_date = datetime.utcnow()
            else:
                remaining = bill.amount_received
                # sort by created_at oldest first
                transactions.sort(key=lambda t: t.created_at)
                for transaction in transactions:
                    if transaction.status == 'paid':
                        continue
                    if remaining >= transaction.commission_amount - 0.01:
                        transaction.status = 'paid'
                        transaction.payment_date = datetime.utcnow()
                        remaining -= transaction.commission_amount
                    else:
                        # leave as pending if not enough funds to cover fully
                        break
            
            db.session.commit()
            
            logger.info(f"Commission payment confirmed for bill {bill_id}")
            return True, "Payment confirmed successfully"
            
        except Exception as e:
            logger.error(f"Error confirming commission payment for bill {bill_id}: {str(e)}")
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def get_commission_config(restaurant_id):
        """Get commission configuration for a restaurant"""
        config = CommissionConfig.query.filter_by(
            restaurant_id=restaurant_id,
            is_active=True
        ).first()
        
        if not config:
            # Create default config
            config = CommissionConfig(
                restaurant_id=restaurant_id,
                commission_type='percentage',
                commission_rate=5.0,  # Default 5%
                minimum_order_amount=50.0,  # 50 KES minimum
                maximum_commission=500.0,  # 500 KES maximum
                is_active=True
            )
            db.session.add(config)
            db.session.commit()
        
        return config
    
    @staticmethod
    def update_commission_config(restaurant_id, commission_type, commission_rate, 
                               minimum_order_amount, maximum_commission):
        """Update commission configuration for a restaurant"""
        try:
            config = CommissionConfig.query.filter_by(
                restaurant_id=restaurant_id,
                is_active=True
            ).first()
            
            if config:
                config.commission_type = commission_type
                config.commission_rate = commission_rate
                config.minimum_order_amount = minimum_order_amount
                config.maximum_commission = maximum_commission
                config.updated_at = datetime.utcnow()
            else:
                config = CommissionConfig(
                    restaurant_id=restaurant_id,
                    commission_type=commission_type,
                    commission_rate=commission_rate,
                    minimum_order_amount=minimum_order_amount,
                    maximum_commission=maximum_commission,
                    is_active=True
                )
                db.session.add(config)
            
            db.session.commit()
            logger.info(f"Updated commission config for restaurant {restaurant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating commission config for restaurant {restaurant_id}: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_pending_commission_bills(restaurant_id=None):
        """Get pending commission bills"""
        try:
            query = CommissionBill.query.filter_by(status='pending')
            
            if restaurant_id:
                query = query.filter_by(restaurant_id=restaurant_id)
            
            bills = query.order_by(CommissionBill.due_date).all()
            return bills
            
        except Exception as e:
            logger.error(f"Error getting pending commission bills: {str(e)}")
            return []
    
    @staticmethod
    def send_commission_reminders():
        """Send reminders for overdue commission payments"""
        try:
            overdue_bills = CommissionBill.query.filter(
                and_(
                    CommissionBill.status == 'pending',
                    CommissionBill.due_date < datetime.utcnow()
                )
            ).all()
            
            for bill in overdue_bills:
                # Update status to overdue
                bill.status = 'overdue'
                
                # Here you would integrate with SMS/email service
                # For now, just log the reminder
                logger.info(f"Commission reminder sent for restaurant {bill.restaurant_id}, "
                          f"amount: {bill.total_commission} KES, due date: {bill.due_date}")
            
            db.session.commit()
            return len(overdue_bills)
            
        except Exception as e:
            logger.error(f"Error sending commission reminders: {str(e)}")
            db.session.rollback()
            return 0 