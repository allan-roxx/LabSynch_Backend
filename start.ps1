Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "         LabSynch Django Helper Commands         " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Activate Virtual Environment:" -ForegroundColor Yellow
Write-Host "   ..\.venv\Scripts\Activate" -ForegroundColor Green
Write-Host "   (Activates the isolated Python environment)"
Write-Host ""

Write-Host "2. Start Development Server:" -ForegroundColor Yellow
Write-Host "   python manage.py runserver" -ForegroundColor Green
Write-Host "   (Starts the server on http://127.0.0.1:8000)"
Write-Host ""

Write-Host "3. Make Migrations:" -ForegroundColor Yellow
Write-Host "   python manage.py makemigrations" -ForegroundColor Green
Write-Host "   (Detects model changes and generates migration files)"
Write-Host ""

Write-Host "4. Apply Migrations:" -ForegroundColor Yellow
Write-Host "   python manage.py migrate" -ForegroundColor Green
Write-Host "   (Applies pending migrations to the database)"
Write-Host ""

Write-Host "5. Create Superuser (Admin):" -ForegroundColor Yellow
Write-Host "   python manage.py createsuperuser" -ForegroundColor Green
Write-Host "   (Creates an admin account to log into the Django admin panel)"
Write-Host ""

Write-Host "6. Run Tests:" -ForegroundColor Yellow
Write-Host "   python -m pytest" -ForegroundColor Green
Write-Host "   (Runs the automated test suite)"
Write-Host ""

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Usage: Just copy/paste any of the green commands and press Enter."
Write-Host ""
