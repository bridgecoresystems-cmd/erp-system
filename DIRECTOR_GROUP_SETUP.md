# 👔 Инструкция по созданию группы "Director" (Начальник)

## Описание

Группа **Director** предоставляет полный доступ ко всем модулям системы:
- ✅ **Сотрудники** (HR) - список, добавление
- ✅ **Рабочее время** - учет и контроль
- ✅ **Безопасность** - панель охраны, отчеты, экспорт
- ✅ **Lohia мониторинг** - дашборд станков, история, статистика
- ✅ **Отчеты** - различные отчеты по системе

При входе начальник **сразу попадает** на страницу `/employees/list/` (список сотрудников).

---

## Создание группы и пользователя

### Вариант 1: Через Django Admin (веб-интерфейс)

#### Шаг 1: Создание группы Director

1. Войдите в админку: `http://your-site.com/admin/`
2. Перейдите в **Authentication and Authorization → Groups**
3. Нажмите **Add Group** (Добавить группу)
4. Заполните:
   - **Name:** `Director` (точно как написано!)
5. **Permissions:** Можно добавить права по желанию (или оставить пустым)
6. Нажмите **Save**

#### Шаг 2: Создание пользователя для начальника

1. В админке перейдите в **Users** (Пользователи)
2. Нажмите **Add User** (Добавить пользователя)
3. Заполните:
   - **Username:** например `director` или `nachalnik`
   - **Password:** установите надежный пароль
4. Нажмите **Save**
5. На странице редактирования пользователя:
   - **First name:** Имя начальника
   - **Last name:** Фамилия начальника
   - **Email:** Email начальника (опционально)
   - **Groups:** Выберите **Director** из списка Available groups и переместите в Chosen groups
   - **Staff status:** ✅ можно отметить (чтобы был доступ в админку)
   - **Superuser status:** ❌ НЕ отмечайте (Director уже дает полный доступ)
6. Нажмите **Save**

#### Шаг 3: Привязка к Employee (опционально)

Если хотите чтобы у начальника была полная карточка сотрудника:

1. Перейдите в **Employees → Employees**
2. Найдите или создайте запись сотрудника для начальника
3. В поле **User** выберите созданного пользователя
4. Заполните остальные поля (фото, отдел, должность и т.д.)
5. Нажмите **Save**

---

### Вариант 2: Через Django Shell (командная строка)

```bash
cd /path/to/erp-system/factory_erp
source ../venv/bin/activate
python manage.py shell
```

Затем выполните:

```python
from django.contrib.auth.models import User, Group
from employees.models import Employee

# 1. Создаем группу Director
director_group, created = Group.objects.get_or_create(name='Director')
if created:
    print("✅ Группа Director создана")
else:
    print("ℹ️ Группа Director уже существует")

# 2. Создаем пользователя начальника
username = 'director'  # Замените на нужное имя
password = 'SecurePassword123'  # Замените на надежный пароль
first_name = 'Иван'  # Замените
last_name = 'Петров'  # Замените

user, created = User.objects.get_or_create(
    username=username,
    defaults={
        'first_name': first_name,
        'last_name': last_name,
        'email': 'director@example.com',  # Опционально
        'is_staff': True,  # Доступ в админку
        'is_superuser': False,  # НЕ суперпользователь
    }
)

if created:
    user.set_password(password)
    user.save()
    print(f"✅ Пользователь {username} создан")
else:
    print(f"ℹ️ Пользователь {username} уже существует")

# 3. Добавляем пользователя в группу Director
user.groups.add(director_group)
user.save()
print(f"✅ Пользователь {username} добавлен в группу Director")

# 4. (Опционально) Создаем Employee профиль
employee, created = Employee.objects.get_or_create(
    user=user,
    defaults={
        'first_name': first_name,
        'last_name': last_name,
        'employee_id': 'DIR001',  # Уникальный ID
        'department': 'Администрация',
        'position': 'Директор',
        'is_active': True,
    }
)

if created:
    print(f"✅ Employee профиль для {username} создан")
else:
    print(f"ℹ️ Employee профиль для {username} уже существует")

print("\n" + "="*50)
print("🎉 Настройка завершена!")
print("="*50)
print(f"Логин: {username}")
print(f"Пароль: {password}")
print(f"URL: http://your-site.com/")
print(f"После входа автоматически перейдет на: /employees/list/")
```

Выйти из shell: `exit()`

---

## Проверка работы

1. **Выйдите** из текущей учетной записи (если залогинены)
2. Войдите под пользователем из группы **Director**
3. ✅ Должны **автоматически** попасть на страницу `/employees/list/`
4. ✅ В меню должны быть видны все разделы:
   - 👥 Сотрудники
   - ⏰ Рабочее время
   - 🛡️ Безопасность
   - 🏭 Станок Lohia
   - 📊 Отчеты

---

## Удаление/изменение

### Удалить пользователя из группы Director:

**Admin:**
1. Users → Выбрать пользователя
2. В разделе Groups удалить Director из Chosen groups
3. Save

**Shell:**
```python
from django.contrib.auth.models import User, Group

user = User.objects.get(username='director')
director_group = Group.objects.get(name='Director')
user.groups.remove(director_group)
user.save()
```

### Удалить группу Director:

**Admin:**
1. Groups → Выбрать Director
2. Delete

**Shell:**
```python
from django.contrib.auth.models import Group

director_group = Group.objects.get(name='Director')
director_group.delete()
```

---

## Безопасность

⚠️ **Важно:**
- Группа Director имеет полный доступ ко всем модулям
- Не добавляйте в эту группу пользователей, которым не нужен полный доступ
- Используйте надежные пароли
- Рассмотрите возможность использования двухфакторной аутентификации

---

## Технические детали

### Измененные файлы:

**`templates/base.html`** (строки 92-129):
- Добавлена проверка группы `Director`
- Отображение всех модулей для начальника

**`employees/views.py`** (строки 331-333):
- Добавлен редирект для группы `Director` → `employees:employee_list`

### Логика работы:

1. Пользователь входит в систему
2. `LOGIN_REDIRECT_URL` отправляет на `/employees/`
3. `HomeView.get()` проверяет группы пользователя
4. Если находит `Director` → редирект на `employees:employee_list`
5. В навигационном меню (base.html) отображаются все разделы

---

## FAQ

**Q: Можно ли изменить имя группы с "Director" на другое?**  
A: Можно, но нужно изменить во всех местах:
- `base.html` (строка 94): `{% if group.name == "Director" %}`
- `views.py` (строка 332): `if 'Director' in user_groups:`

**Q: Можно ли у пользователя несколько групп?**  
A: Да, но приоритет по редиректу идет сверху вниз:
1. Director
2. HR_Admins
3. HR_Users
4. Security
5. Security_Users

**Q: Что если начальник хочет попадать на другую страницу?**  
A: Измените строку 333 в `views.py`:
```python
return redirect('lohia_monitor:dashboard')  # Например, на Lohia дашборд
```

---

## 🎉 Готово!

Теперь у начальника полный доступ ко всей системе с автоматическим переходом на список сотрудников при входе.

