from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, FileField, SelectField, BooleanField, IntegerField, DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange, Optional, URL
import re

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Reset Password')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message="Please enter a valid email address")
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message="Please enter a valid email address")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message="Password must be at least 6 characters long")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match")
    ])
    # Removed restaurant_id field
    restaurant_name = StringField('Restaurant Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message="Restaurant name must be between 2 and 100 characters")
    ])
    currency = SelectField('Currency', choices=[
        ('USD', 'US Dollar ($)'),
        ('KES', 'Kenyan Shilling (KSh)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        ('INR', 'Indian Rupee (₹)'),
        ('AUD', 'Australian Dollar (A$)'),
        ('CAD', 'Canadian Dollar (C$)'),
        ('JPY', 'Japanese Yen (¥)')
    ], validators=[DataRequired()])
    logo = FileField('Restaurant Logo')

class RegistrationVerificationForm(FlaskForm):
    verification_code = StringField('Verification Code', validators=[
        DataRequired(),
        Length(min=4, max=10, message="Enter the code sent to your email")
    ])
    submit = SubmitField('Verify')

class MenuItemForm(FlaskForm):
    name = StringField('Item Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message="Item name must be between 2 and 100 characters")
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(max=500, message="Description cannot exceed 500 characters")
    ])
    price = FloatField('Price', validators=[
        DataRequired(),
        NumberRange(min=0, message="Price must be greater than or equal to 0")
    ])
    item_image = FileField('Item Image')
    image_url = StringField('Image URL')
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    stock = IntegerField('Stock', validators=[NumberRange(min=0)], default=0)

class DeleteForm(FlaskForm):
    item_id = StringField('Item ID', validators=[DataRequired()])
    submit = SubmitField('Delete')


class ProfileForm(FlaskForm):
    # Restaurant Information
    restaurant_name = StringField('Restaurant Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message="Restaurant name must be between 2 and 100 characters")
    ])
    restaurant_description = TextAreaField('Restaurant Description', validators=[
        Optional(),
        Length(max=500, message="Description cannot exceed 500 characters")
    ])
    restaurant_address = StringField('Restaurant Address', validators=[
        Optional(),
        Length(max=200, message="Address cannot exceed 200 characters")
    ])
    opening_hours = StringField('Opening Hours', validators=[
        Optional(),
        Length(max=200, message="Opening hours cannot exceed 200 characters")
    ])
    currency = SelectField('Currency', choices=[
        ('USD', 'US Dollar ($)'),
        ('KES', 'Kenyan Shilling (KSh)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        ('INR', 'Indian Rupee (₹)'),
        ('AUD', 'Australian Dollar (A$)'),
        ('CAD', 'Canadian Dollar (C$)'),
        ('JPY', 'Japanese Yen (¥)')
    ], validators=[DataRequired()])
    logo = FileField('Restaurant Logo', validators=[Optional()])

    # Contact Information
    contact_phone = StringField('Contact Phone Number', validators=[
        Optional(),
        Length(min=10, max=20, message="Phone number must be between 10 and 20 characters")
    ], render_kw={"type": "tel", "id": "contact_phone", "class": "form-control intl-phone-input"})
    help_contact = StringField('Help Contact Number', validators=[
        Optional(),
        Length(min=10, max=20, message="Phone number must be between 10 and 20 characters")
    ], render_kw={"type": "tel", "id": "help_contact", "class": "form-control intl-phone-input"})

    # Website and Social Media
    website = StringField('Website', validators=[Optional(), URL(message="Please enter a valid URL")])
    social_media = TextAreaField('Social Media Links (JSON)', validators=[Optional(), Length(max=1000, message="Social media JSON too long")])

    submit = SubmitField('Save Profile')

    def validate_on_submit(self):
        return super().validate_on_submit()

class SettingsForm(FlaskForm):
    # Payment Settings
    payment_method = SelectField('Preferred Payment Method', choices=[
        ('stk_push', 'STK Push (Automatic)'),
        ('manual', 'Manual Payment')
    ], validators=[DataRequired()])
    
    # Manual Payment Details
    mpesa_receiving_method = SelectField('Mpesa Receiving Method', choices=[
        ('paybill', 'Paybill'),
        ('till', 'Till Number'),
        ('phone', 'Personal Phone Number')
    ], validators=[Optional()])
    
    mpesa_paybill = StringField('Mpesa Paybill Number', validators=[
        Optional(),
        Length(min=5, max=7, message="Paybill number must be 5-7 digits")
    ])
    
    mpesa_till = StringField('Mpesa Till Number', validators=[
        Optional(),
        Length(min=5, max=7, message="Till number must be 5-7 digits")
    ])
    
    mpesa_phone_receiver = StringField('Mpesa Phone Number', validators=[
        Optional()
    ])

    # Display Settings
    theme_color = StringField('Theme Color', validators=[
        Optional(),
        Length(max=20)
    ])
    menu_layout = SelectField('Menu Layout', choices=[
        ('grid', 'Grid View'),
        ('list', 'List View')
    ])
    show_prices = BooleanField('Show Prices')
    show_descriptions = BooleanField('Show Descriptions')
    language = SelectField('Language', choices=[
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('it', 'Italian'),
        ('pt', 'Portuguese'),
        ('ru', 'Russian'),
        ('zh', 'Chinese'),
        ('ja', 'Japanese'),
        ('ko', 'Korean')
    ])
    timezone = SelectField('Timezone', choices=[
        ('UTC', 'UTC'),
        ('America/New_York', 'Eastern Time'),
        ('America/Chicago', 'Central Time'),
        ('America/Denver', 'Mountain Time'),
        ('America/Los_Angeles', 'Pacific Time'),
        ('Europe/London', 'London'),
        ('Europe/Paris', 'Paris'),
        ('Asia/Tokyo', 'Tokyo'),
        ('Asia/Shanghai', 'Shanghai'),
        ('Australia/Sydney', 'Sydney')
    ])

    # Account Settings
    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[
        Optional(),
        Length(min=6, message="Password must be at least 6 characters long")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        Optional(),
        EqualTo('new_password', message="Passwords must match")
    ])

    submit = SubmitField('Save Settings')

    def validate_on_submit(self):
        if not super().validate_on_submit():
            return False

        # Validate manual payment details if manual payment is selected
        if self.payment_method.data == 'manual':
            method = self.mpesa_receiving_method.data
            if not method:
                self.mpesa_receiving_method.errors.append('Please select a receiving method for manual payments.')
                return False

            if method == 'paybill' and not self.mpesa_paybill.data:
                self.mpesa_paybill.errors.append('Paybill number is required when using Paybill.')
                return False
            if method == 'till' and not self.mpesa_till.data:
                self.mpesa_till.errors.append('Till number is required when using Till Number.')
                return False
            if method == 'phone':
                if not self.mpesa_phone_receiver.data:
                    self.mpesa_phone_receiver.errors.append('Phone number is required when using Personal Phone Number.')
                    return False
                # Remove any non-digit characters
                number = re.sub(r'\D', '', self.mpesa_phone_receiver.data)
                # Check length
                if len(number) < 10 or len(number) > 15:
                    self.mpesa_phone_receiver.errors.append('Phone number must be between 10 and 15 digits.')
                    return False
                # Check if the number starts with 254 or 0
                if number.startswith('254'):
                    number = number[3:]
                elif number.startswith('0'):
                    number = number[1:]
                # Validate Kenyan phone number format
                if not re.match(r'^[7-9][0-9]{8}$', number):
                    self.mpesa_phone_receiver.errors.append('Please enter a valid Kenyan phone number.')
                    return False

        return True

class DarajaCredentialsForm(FlaskForm):
    consumer_key = StringField('Consumer Key', validators=[DataRequired()])
    consumer_secret = StringField('Consumer Secret', validators=[DataRequired()])
    shortcode = StringField('Shortcode', validators=[DataRequired()])
    passkey = StringField('Passkey', validators=[DataRequired()])
    environment = SelectField('Environment', choices=[
        ('sandbox', 'Sandbox (Testing)'),
        ('production', 'Production (Live)')
    ], default='sandbox')
    submit = SubmitField('Save Credentials')
    
    def validate_shortcode(self, shortcode):
        """Validate that shortcode is numeric and has correct length"""
        if not shortcode.data.isdigit():
            raise ValidationError('Shortcode must contain only numbers')
        if len(shortcode.data) not in [5, 6, 7]:  # Standard M-Pesa shortcode lengths
            raise ValidationError('Shortcode must be 5-7 digits long')

class PlatformSettingsForm(FlaskForm):
    callback_url_sandbox = StringField('Sandbox Callback URL', validators=[DataRequired()])
    callback_url_production = StringField('Production Callback URL', validators=[Optional()])
    submit = SubmitField('Save Settings')

# Feedback Form
class FeedbackForm(FlaskForm):
    email = StringField('Email', validators=[Optional(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')

# Help Info Form
class HelpInfoForm(FlaskForm):
    email = StringField('Support Email', validators=[Optional(), Email()])
    phone = StringField('Support Phone', validators=[Optional()])
    other = TextAreaField('Other Information', validators=[Optional()])
    submit = SubmitField('Save Help Information')

# Admin Login Form
class AdminLoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message="Please enter a valid email address")
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class SetAdminPanelPasswordForm(FlaskForm):
    password = PasswordField('Set Admin Panel Password', validators=[DataRequired(), Length(min=4, max=32)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Set Password')

class AdminPanelPasswordForm(FlaskForm):
    password = PasswordField('Admin Panel Password', validators=[DataRequired()])
    submit = SubmitField('Enter') 

class ChangeAdminPanelPasswordForm(FlaskForm):
    current_password = PasswordField('Current Admin Panel Password', validators=[DataRequired()])
    new_password = PasswordField('New Admin Panel Password', validators=[DataRequired(), Length(min=4, max=32)])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Change Password')

class ResetAdminPanelPasswordForm(FlaskForm):
    main_account_password = PasswordField('Main Account Password', validators=[DataRequired()])
    new_password = PasswordField('New Admin Panel Password', validators=[DataRequired(), Length(min=4, max=32)])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Reset Password') 

class CommissionConfigForm(FlaskForm):
    commission_type = SelectField('Commission Type', choices=[
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount')
    ], validators=[DataRequired()])
    commission_rate = FloatField('Commission Rate', validators=[DataRequired()])
    minimum_order_amount = FloatField('Minimum Order Amount (KES)', default=50.0)
    maximum_commission = FloatField('Maximum Commission (KES)', default=500.0)
    submit = SubmitField('Save Commission Configuration')

class CommissionBillForm(FlaskForm):
    payment_reference = StringField('Payment Reference', validators=[DataRequired()])
    amount_received = FloatField('Amount Received (KES)', validators=[DataRequired()])
    submit = SubmitField('Confirm Payment')

class CommissionReportForm(FlaskForm):
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    restaurant_id = SelectField('Restaurant', coerce=int, validators=[Optional()])
    submit = SubmitField('Generate Report') 