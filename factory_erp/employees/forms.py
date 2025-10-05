# employees/forms.py
from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError
from .models import Employee
import re

class EmployeeForm(forms.ModelForm):
    """Расширенная форма для добавления и редактирования сотрудника"""
    
    class Meta:
        model = Employee
        fields = [
            'user',
            # Основные данные
            'first_name', 'last_name', 'middle_name',
            # Персональные данные
            'birth_date', 'gender', 'marital_status',
            # Контактные данные
            'phone', 'email', 'address',
            # Документы
            'passport_series', 'passport_number', 'passport_issued_date', 'passport_issued_by',
            'inn', 'snils',
            # Рабочие данные
            'department', 'position', 'employee_id', 'hire_date',
            # Дополнительно
            'rfid_uid', 'photo', 'is_active'
        ]
        
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-control'
            }),
            # ОСНОВНЫЕ ДАННЫЕ
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Введите фамилию',
                'required': True
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите отчество (необязательно)'
            }),
            
            # ПЕРСОНАЛЬНЫЕ ДАННЫЕ
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }),
            'marital_status': forms.Select(attrs={
                'class': 'form-control'
            }),
            
            # КОНТАКТНЫЕ ДАННЫЕ
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+993 65 12 34 56'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@company.com'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Полный адрес проживания',
                'rows': 3
            }),
            
            # ПАСПОРТНЫЕ ДАННЫЕ
            'passport_series': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'I-AH',
                'style': 'text-transform: uppercase;',
                'maxlength': 4
            }),
            'passport_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '123456',
                'maxlength': 6
            }),
            'passport_issued_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'passport_issued_by': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Кем выдан паспорт',
                'rows': 2
            }),
            
            # НАЛОГОВЫЕ ДАННЫЕ
            'inn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1234567890 или 123456789012',
                'maxlength': 12
            }),
            'snils': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12345678901',
                'maxlength': 11
            }),
            
            # РАБОЧИЕ ДАННЫЕ
            'department': forms.Select(attrs={
                'class': 'form-control'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите должность',
                'required': True
            }),
            'employee_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Табельный номер (автоматически)',
                'readonly': True
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }, format='%Y-%m-%d'),

            # ДОПОЛНИТЕЛЬНО
            'rfid_uid': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Приложите карту к считывателю',
                'maxlength': 20,
                'style': 'text-transform: uppercase;'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels = {
            'user': 'Пользователь системы',
            # Основные данные
            'first_name': 'Имя *',
            'last_name': 'Фамилия *',
            'middle_name': 'Отчество',
            # Персональные данные
            'birth_date': 'Дата рождения',
            'gender': 'Пол',
            'marital_status': 'Семейное положение',
            # Контактные данные
            'phone': 'Телефон',
            'email': 'Email',
            'address': 'Адрес проживания',
            # Документы
            'passport_series': 'Серия паспорта',
            'passport_number': 'Номер паспорта',
            'passport_issued_date': 'Дата выдачи паспорта',
            'passport_issued_by': 'Кем выдан паспорт',
            'inn': 'ИНН',
            'snils': 'СНИЛС',
            # Рабочие данные
            'department': 'Цех/Отдел *',
            'position': 'Должность *',
            'employee_id': 'Табельный номер',
            'hire_date': 'Дата приема *',
            # Дополнительно
            'rfid_uid': 'RFID карта',
            'photo': 'Фотография',
            'is_active': 'Активен'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Форматируем дату для HTML input при редактировании
        if self.instance.pk:
            if self.instance.hire_date:
                self.fields['hire_date'].widget.attrs['value'] = self.instance.hire_date.strftime('%Y-%m-%d')
            if self.instance.birth_date:
                self.fields['birth_date'].widget.attrs['value'] = self.instance.birth_date.strftime('%Y-%m-%d')
            if self.instance.passport_issued_date:
                self.fields['passport_issued_date'].widget.attrs['value'] = self.instance.passport_issued_date.strftime('%Y-%m-%d')
        
        # Генерируем табельный номер для нового сотрудника
        if not self.instance.pk:  # Новый сотрудник
            self.fields['employee_id'].initial = self.generate_employee_id()
            self.fields['is_active'].initial = True
        
        # Список цехов/отделов
        DEPARTMENT_CHOICES = [
            ('', 'Выберите цех/отдел'),
            ('Механики', 'Механики'),
            ('Сотрудник', 'Сотрудник'),
            ('Сотрудник_bag', 'Сотрудник_bag'),
            ('IT отдел', 'IT отдел'),
            ('Бухгалтерия', 'Бухгалтерия'),
            ('Администрация', 'Администрация'),
            ('Склад', 'Склад'),
            ('Охрана', 'Охрана'),
        ]
        self.fields['department'].widget.choices = DEPARTMENT_CHOICES
        
        # Выбор пола
        GENDER_CHOICES = [
            ('', 'Не указан'),
            ('M', 'Мужской'),
            ('F', 'Женский'),
        ]
        self.fields['gender'].widget.choices = GENDER_CHOICES
        
        # Выбор семейного положения
        MARITAL_CHOICES = [
            ('', 'Не указано'),
            ('single', 'Холост/Не замужем'),
            ('married', 'Женат/Замужем'),
            ('divorced', 'Разведен(а)'),
            ('widowed', 'Вдовец/Вдова'),
        ]
        self.fields['marital_status'].widget.choices = MARITAL_CHOICES
        
        if 'user' in self.fields:
            print("DEBUG: Поле user найдено в форме")  # Для отладки
            self.fields['user'].required = False
            self.fields['user'].queryset = User.objects.all()
            self.fields['user'].empty_label = "Не назначен"
        else:
            print("DEBUG: Поле user НЕ найдено в форме!")  # Для отладки
        
    
    def generate_employee_id(self):
        """Генерирует уникальный табельный номер"""
        # Находим последний табельный номер
        last_employee = Employee.objects.filter(
            employee_id__regex=r'^\d+$'
        ).order_by('employee_id').last()
        
        if last_employee and last_employee.employee_id.isdigit():
            next_id = int(last_employee.employee_id) + 1
        else:
            next_id = 1001  # Начинаем с 1001
        
        return str(next_id).zfill(4)  # Дополняем нулями до 4 символов
    
    def clean_first_name(self):
        """Валидация имени"""
        first_name = self.cleaned_data.get('first_name', '').strip()
        if not first_name:
            raise ValidationError('Имя обязательно для заполнения')
        
        if len(first_name) < 2:
            raise ValidationError('Имя должно содержать минимум 2 символа')
        
        if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s-]+$', first_name):
            raise ValidationError('Имя может содержать только буквы, пробелы и дефисы')
        
        return first_name.title()
    
    def clean_last_name(self):
        """Валидация фамилии"""
        last_name = self.cleaned_data.get('last_name', '').strip()
        if not last_name:
            raise ValidationError('Фамилия обязательна для заполнения')
        
        if len(last_name) < 2:
            raise ValidationError('Фамилия должна содержать минимум 2 символа')
        
        if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s-]+$', last_name):
            raise ValidationError('Фамилия может содержать только буквы, пробелы и дефисы')
        
        return last_name.title()
    
    def clean_middle_name(self):
        """Валидация отчества"""
        middle_name = self.cleaned_data.get('middle_name', '').strip()
        if middle_name:
            if len(middle_name) < 2:
                raise ValidationError('Отчество должно содержать минимум 2 символа')
            
            if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s-]+$', middle_name):
                raise ValidationError('Отчество может содержать только буквы, пробелы и дефисы')
            
            return middle_name.title()
        return middle_name
    
    def clean_phone(self):
        """Валидация телефона"""
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            # Убираем все кроме цифр и +
            cleaned_phone = re.sub(r'[^\d+]', '', phone)
            if not re.match(r'^\+?[\d]{10,15}$', cleaned_phone):
                raise ValidationError('Неверный формат телефона. Используйте формат: +7XXXXXXXXXX')
            return cleaned_phone
        return phone
    
    def clean_rfid_uid(self):
        """Валидация RFID"""
        rfid_uid = self.cleaned_data.get('rfid_uid', '').strip().upper()
        
        if rfid_uid:
            # Проверяем формат RFID (обычно 8-10 символов hex)
            if not re.match(r'^[0-9A-F]{8,14}$', rfid_uid):
                raise ValidationError('RFID должен содержать 8-14 символов в формате HEX (0-9, A-F)')
            
            # Проверяем уникальность
            existing_employee = Employee.objects.filter(rfid_uid=rfid_uid).exclude(pk=self.instance.pk).first()
            if existing_employee:
                raise ValidationError(f'Эта RFID карта уже привязана к сотруднику: {existing_employee.get_full_name()}')
        
        return rfid_uid
    
    def clean_employee_id(self):
        """Валидация табельного номера"""
        employee_id = self.cleaned_data.get('employee_id', '').strip()
        
        if not employee_id:
            raise ValidationError('Табельный номер обязателен')
        
        # Проверяем уникальность
        existing_employee = Employee.objects.filter(employee_id=employee_id).exclude(pk=self.instance.pk).first()
        if existing_employee:
            raise ValidationError(f'Табельный номер уже используется сотрудником: {existing_employee.get_full_name()}')
        
        return employee_id
    
    def clean_position(self):
        """Валидация должности"""
        position = self.cleaned_data.get('position', '').strip()
        if not position:
            raise ValidationError('Должность обязательна для заполнения')
        
        if len(position) < 3:
            raise ValidationError('Должность должна содержать минимум 3 символа')
        
        return position.title()
    
    def clean_photo(self):
        """Валидация фотографии"""
        photo = self.cleaned_data.get('photo')
        
        if photo and hasattr(photo, 'content_type'):
            # Проверяем размер файла (максимум 5МБ)
            if photo.size > 5 * 1024 * 1024:
                raise ValidationError('Размер фотографии не должен превышать 5МБ')
            
            # Проверяем формат
            if not photo.content_type.startswith('image/'):
                raise ValidationError('Файл должен быть изображением')
        
        return photo