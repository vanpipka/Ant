// Функция для очистки строки от символов валюты и превращения в число
const parseCurrency = (text) => {
        return parseFloat(text.replace(/[^0-9.-]+/g, "")) || 0;
};

// Функция форматирования числа обратно в валюту
const formatCurrency = (value) => {
        return value.toLocaleString('ru-RU', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }) + '₽'; // Добавляем символ рубля для отображения
};

// Главная функция пересчета всего инвойса
const updateInvoiceTotals = () => {
    
    let totalAmount = document.querySelector('#total-amount');
    let subtotal = 0;

    if (!totalAmount) return;

    // 1. Считаем каждую строку
    document.querySelectorAll('table tbody tr.order-row').forEach(row => {

        const qty = parseInt(row.querySelector('.qty-input').value) || 0;
            
        const unitPrice = parseCurrency(row.querySelector('.order-unit-price').innerText);
            
        const amount = qty * unitPrice;
        subtotal += amount;

        // Обновляем Amount в строке
        const amountCell = row.querySelector('.order-unit-amount');
        if (amountCell) {
            amountCell.innerText = formatCurrency(amount);
        }
    });

    // 2. Считаем налоги и скидки (берем проценты из текста или захардкодим)

    // 3. Обновляем итоговую таблицу в DOM
    document.querySelector('#total-amount').innerText = formatCurrency(subtotal);
};

// Функция загрузки и фильтрации товаров
async function loadProducts(query = '') {
    const listContainer = document.getElementById('product-list-results');
    listContainer.innerHTML = '<div class="text-center p-3"><div class="spinner-border spinner-border-sm"></div></div>';

    try {
        // Замените URL на ваш эндпоинт, который отдает JSON товаров
        const response = await fetch(`/api/orders/products/?q=${query}`);
        const products = await response.json();

        listContainer.innerHTML = '';
        products.forEach(product => {
            const item = document.createElement('div');
            item.className = 'list-group-item d-flex justify-content-between align-items-center list-group-item-action';
            item.innerHTML = `
                <div>
                    <div class="fw-bold">${product.name}</div>
                    <small class="text-muted">Арт: ${product.product_id} | ${product.price}₽</small>
                </div>
                <button class="btn btn-sm btn-outline-primary select-product-btn" 
                        data-id="${product.product_id}" 
                        data-name="${product.name}" 
                        data-price="${product.price}">
                    Добавить
                </button>
            `;
            listContainer.appendChild(item);
        });
    } catch (err) {
        listContainer.innerHTML = '<div class="p-3 text-danger">Ошибка загрузки товаров</div>';
    }
}

// Поиск "на лету"
//document.getElementById('product-search-input').addEventListener('input', (e) => {
//    loadProducts(e.target.value);
//});

// Инициализация тултипов и поповеров Bootstrap (если понадобятся)
document.addEventListener('DOMContentLoaded', function () {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Пример: закрытие алертов через 5 секунд
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Запрещаем ввод нечисловых символов в инпут вручную
document.addEventListener('input', function(e) {
    if (e.target.classList.contains('qty-input')) {
        e.target.value = e.target.value.replace(/[^0-9]/g, '');
        if (e.target.value === '' || e.target.value === '0') {
            e.target.value = 1;
        }
    }
});

document.addEventListener('DOMContentLoaded', function() {
    
    // Слушаем событие 'change', которое вылетает из вашего скрипта кнопок
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('qty-input')) {
            updateInvoiceTotals();
        }
    });

    // Инициализация при загрузке (чтобы суммы сразу были верные)
    updateInvoiceTotals();
});

// Используем делегирование для динамически подгруженного контента
document.addEventListener('change', function(e) {
    // Проверяем, что событие произошло именно на списке клиентов
    if (e.target && e.target.id === 'client-select') {
        const clientId = e.target.value;
        const addressSelect = document.getElementById('address-select');

        if (!clientId || !addressSelect) return;

        // Показываем состояние загрузки в поле адреса
        addressSelect.disabled = true;
        addressSelect.innerHTML = '<option>Загрузка адресов...</option>';

        // Отправляем запрос на сервер
        fetch(`/api/orders/addresses/?client_id=${clientId}`)
            .then(response => response.json())
            .then(data => {
                addressSelect.innerHTML = '<option value="" selected disabled>Выберите адрес доставки</option>';
                
                data.forEach(addr => {
                    const option = document.createElement('option');
                    option.value = addr.id;
                    option.textContent = addr.address_line;
                    addressSelect.appendChild(option);
                });

                addressSelect.disabled = false;
            })
            .catch(error => {
                console.error('Ошибка:', error);
                addressSelect.innerHTML = '<option>Ошибка загрузки</option>';
            });
    }
});

document.addEventListener('click', function(e) {
    // Проверяем, нажата ли иконка корзины или кнопка с классом bi-trash
    if (e.target.classList.contains('bi-trash') || e.target.closest('.bi-trash')) {
        
        // Находим строку, в которой находится кнопка
        const row = e.target.closest('.order-row');
        
        if (row) {
            // Добавим небольшое подтверждение перед удалением (опционально)
            if (confirm('Вы уверены, что хотите удалить эту позицию?')) {
                
                // Удаляем строку из DOM
                row.remove();
                
                // ВАЖНО: вызываем функцию пересчета, которую мы написали в прошлом шаге
                updateInvoiceTotals();
            }
        }
    }
    // Проверяем, нажата ли кнопка плюс или минус
    if (e.target.classList.contains('qty-btn')) {
        const container = e.target.closest('.qty-control');
        const input = container.querySelector('.qty-input');
        let currentValue = parseInt(input.value) || 0;

        console.log('Текущая qty:', currentValue);
        if (e.target.innerText === '+') {
            input.value = currentValue + 1;
        } else if (e.target.innerText === '-') {
            if (currentValue > 1) {
                input.value = currentValue - 1;
            }
        }

        // Вызываем событие 'change' вручную, чтобы другие скрипты 
        // (например, пересчет суммы) узнали об изменении
        input.dispatchEvent(new Event('change', { bubbles: true }));
    }
    // Проверим нажата ли кнопка подбора товаров (может быть иконка, может быть кнопка с id)
    if (e.target.closest('#add-item-btn')) {
        const pickerModal = new bootstrap.Modal(document.getElementById('productPickerModal'));
        pickerModal.show();
        loadProducts(); // Подгружаем список при открытии
    }
    // Проверяем, нажата ли кнопка "Добавить" в списке товаров
    const btn = e.target.closest('.select-product-btn');
    if (btn) {
        const product = {
            id: btn.dataset.id,
            name: btn.dataset.name,
            price: btn.dataset.price
        };

        const tbody = document.querySelector('#order-items-container');
        const newRow = document.createElement('tr');
        newRow.className = 'order-row';
        
        newRow.innerHTML = `
                        <td class="py-4">
                            <div class="fw-bold"></div>
                            <small class="text-muted">${product.name}</small>
                            <input type="hidden" name="product_id" value="${product.id}">
                        </td>
                        <td>
                            <div class="qty-control mx-auto">
                                <button type="button" class="qty-btn">-</button>
                                <input type="text" class="qty-input" value="1">
                                <button type="button" class="qty-btn">+</button>
                            </div>
                        </td>
                        <td class="text-end fw-bold text-muted order-unit-price">${product.price}₽</td>
                        <td class="text-end fw-bold order-unit-amount">${product.price}₽</td>
                        <td class="text-end">
                            <i class="bi bi-trash trash-btn"></i>
                        </td>
        `;

        tbody.appendChild(newRow);
        updateInvoiceTotals(); // Ваш пересчет итогов
        
        // Закрываем модалку выбора после добавления (по желанию)
        // bootstrap.Modal.getInstance(document.getElementById('productPickerModal')).hide();
    }
});

document.addEventListener('DOMContentLoaded', function() {
    
    const orderModal = new bootstrap.Modal(document.getElementById('orderModal'));
    const modalContent = document.getElementById('orderModalContent');

    // Делегирование: слушаем клики по кнопкам "Создать" или "Редактировать"
    document.addEventListener('click', function(e) {

        console.log('Клик по элементу:', e.target);
        const btn = e.target.closest('.open-order-modal');
        if (btn) {
            e.preventDefault();
            const url = btn.getAttribute('href') || btn.dataset.url;

            // Показываем спиннер перед загрузкой
            modalContent.innerHTML = '<div class="p-5 text-center"><div class="spinner-border text-primary"></div></div>';
            orderModal.show();

            // Загружаем HTML
            fetch(url)
                .then(response => response.text())
                .then(html => {
                    modalContent.innerHTML = html;
                    // После вставки HTML нужно заново инициализировать JS (пересчеты, маски и т.д.)
                    if (typeof updateInvoiceTotals === "function") updateInvoiceTotals();
                })
                .catch(error => {console.log(error)});
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    
    const filterForm = document.getElementById('filter-form');

    if (!filterForm) return;
    
    const statusSelect = document.getElementById('status-select');
    const searchInput = document.getElementById('search-input');
    
    // 1. Статус изменили — сразу отправляем
    statusSelect.addEventListener('change', () => filterForm.submit());

    // 2. Поиск с задержкой (Debounce)
    let timeout = null;
    searchInput.addEventListener('input', function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            filterForm.submit();
        }, 600); // Обновит через 0.6 сек после того, как пользователь замолчит
    });
    
    // Фокус в конец строки при вводе (чтобы курсор не прыгал при обновлении страницы)
    if (searchInput.value) {
        searchInput.focus();
        const val = searchInput.value;
        searchInput.value = '';
        searchInput.value = val;
    }
});