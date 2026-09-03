const CACHE_ITEMS_KEY = 'last_selected_items';

async function submitFormInBackground() {
   
    const finalStatusInput = document.getElementById('final-status');
    finalStatusInput.value = 'draft';
    await submitForm(null, true);

}

async function submitForm(confirmModal, its_backround_submit = false) {

    const mainForm = document.getElementById('order-main-form');
    if (!mainForm) return;

    if (!mainForm.reportValidity()) {
        return;
    }

    if (confirmModal) {
        confirmModal.hide();
    }

    if (its_backround_submit){
        const formData = new FormData(mainForm);

        formData.append("its_backround_submit", true);

        fetch(mainForm.action, {
            method: mainForm.method || 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(res => {
            if (!res.ok) throw new Error('Save failed');
            return res.json();
        })
        .then(data => {
        
            const current_order_id_element = document.getElementById('current_order_id');
            if (current_order_id_element){
                current_order_id_element.value = data.order_id;
            }
            
        })
        .catch(err => {
            console.error(err);
        });


    }
    else {
        mainForm.submit()
    }
}

// Функция для кастомного селекта подбора номенклатуры
// 1. Инициализация при открытии - показываем последние 5 из кэша
function renderInitialList(container) {
    const cache = JSON.parse(localStorage.getItem(CACHE_ITEMS_KEY) || '[]');
    console.log(cache)
    renderItems(cache, container);
}

// 2. Рендер списка
function renderItems(items, container) {

        if (!container) return;
        const resultsList = container.querySelector('#results-list');

        resultsList.innerHTML = '';
        if (items.length === 0) {
            resultsList.innerHTML = '<div class="text-muted p-2 small">Ничего не найдено</div>';
            return;
        }
        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'dropdown-item p-2 cursor-pointer rounded';
            div.style.cursor = 'pointer';
            div.textContent = item.name;
            div.onclick = () => selectItem(item, container);
            resultsList.appendChild(div);
        });
}

// 3. Логика выбора и кэширования
function selectItem(item, container) {
    
    // console.log('Выбран товар:', item);

    // Здесь можно добавить логику добавления товара в заказ
    const row = container.closest('.order-row');
    const price = row.querySelector('.order-unit-price');
    const hiddenPrice = row.querySelector('[name="item_price"]');
    const display = container.querySelector('.select-display-trigger');
    const hiddenInput = container.querySelector('input[type="hidden"]');
    const dropdown = container.querySelector('.select-item-dropdown-menu');
    

    display.textContent = item.name;
    price.textContent = `${item.price}₽`;
    hiddenPrice.value = item.price;
    hiddenInput.value = item.product_id; // Здесь сохранится ID выбранной страны
    dropdown.style.display = 'none';

    // Если вам нужно сделать что-то еще с ID строки:
    const rowId = display.getAttribute('data-row-id');
    // console.log(`Выбрано в строке №${rowId}: ${item.name}`);

    // Сохраняем в кэш (LocalStorage)
    let cache = JSON.parse(localStorage.getItem(CACHE_ITEMS_KEY) || '[]');

    cache = [item, ...cache.filter(i => i.product_id !== item.product_id)].slice(0, 5);
    localStorage.setItem(CACHE_ITEMS_KEY, JSON.stringify(cache));

    updateInvoiceTotals();

}

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
    const clientId = document.getElementById('client-select').value;

    listContainer.innerHTML = '<div class="text-center p-3"><div class="spinner-border spinner-border-sm"></div></div>';

    try {
        // Замените URL на ваш эндпоинт, который отдает JSON товаров
        const response = await fetch(`/api/products/search/?client_id=${clientId}&q=${query}`);
        const data = await response.json();

        listContainer.innerHTML = '';
        data.results.forEach(product => {
            const item = document.createElement('div');
            item.className = 'list-group-item d-flex justify-content-between align-items-center list-group-item-action';
            item.innerHTML = `
                <div>
                    <div class="fw-bold">${product.name}</div>
                    <small class="text-muted">Артикул: ${product.article}</small>
                </div>
                <div class="qty-control mx-auto">
                    <button type="button" class="qty-btn">-</button>
                        <input type="text" name="item_quantity" class="qty-input" value="1">
                    <button type="button" class="qty-btn">+</button>
                </div>
                <button 
                    class="icon-link nav-link select-product-btn"
                    data-id="${product.product_id}" 
                    data-name="${product.name}" 
                    data-price="${product.client_price}">
                    data-code="${product.article}"> 
                        <i class="bi bi-cart4"></i>
                        В заказ
                </button>
            `;
            listContainer.appendChild(item);
        });
    } catch (err) {
        listContainer.innerHTML = '<div class="p-3 text-danger">Ошибка загрузки товаров</div>';
    }
}

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
    else if (e.target.id === 'product-search-input') {
        //loadProductsV1(e.target.value);
    };
});

// Пересчет сумм
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

// Выбор адреса в заказе
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
                    option.value = addr.address_line;
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

        // console.log('Текущая qty:', currentValue);
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

        // Сохраним ордер
        submitFormInBackground() 
    }

    // Проверим нажата ли кнопка подбора товаров (может быть иконка, может быть кнопка с id)
    if (e.target.closest('#add-item-btn')) {
        
        const tbody = document.querySelector('#order-items-container');
        const nextIndex = tbody.querySelectorAll('.order-row').length + 1;
        const newRow = document.createElement('tr');
        newRow.className = 'order-row';
        
        newRow.innerHTML = `
                        <td class="py-4">
                            <div class="custom-select-container position-relative" style="">
                                <div 
                                    id="select-item-display-${nextIndex}" 
                                    data-row-id="${nextIndex}"
                                    class="select-display-trigger form-select py-3 bg-light border-0 cursor-pointer" 
                                    style="border-radius: 12px;">
                                    Выберите позицию
                                </div>
                                                    
                                <input type="hidden" id="item_product_id_${nextIndex}" name="item_product_id" value="">

                                <div 
                                    id="select-dropdown${nextIndex}"               
                                    class="select-item-dropdown-menu dropdown-menu shadow-lg border-0 w-100 mt-2 p-2" 
                                    style="border-radius: 12px; display: none;">
                                    <input type="text" id="select-search" class="form-control mb-2 p-2 border-0 bg-light" placeholder="Поиск..." autocomplete="off">
                                                        
                                    <div id="results-list" style="max-height: 300px; overflow-y: auto;">
                                    </div>
                                </div>
                            </div>
                        </td>
                        <td>
                            <div class="qty-control mx-auto">
                                <button type="button" class="qty-btn">-</button>
                                <input type="text" name="item_quantity" class="qty-input" value="1">
                                <button type="button" class="qty-btn">+</button>
                            </div>
                        </td>
                        <td class="text-end fw-bold text-muted">
                            <div class="order-unit-price">
                                0.00₽
                            </div>
                            <input type="hidden" name="item_price" value="0.00">    
                        </td>
                        <td class="text-end fw-bold order-unit-amount">0.00₽</td>
                        <td class="text-end">
                            <i class="bi bi-trash trash-btn"></i>
                        </td>
        `;

        tbody.appendChild(newRow);

        // Ниже - вариант с модальной формой для выбора товара. 
        /*
        const pickerModal = new bootstrap.Modal(document.getElementById('productPickerModal'));
        pickerModal.show();
        loadProducts(); // Подгружаем список при открытии
        */
        // Сохраним ордер
        submitFormInBackground() 
    }else if (e.target.closest('#add-item-btn-offcanvas')) {
        //SelectProductsHandler();  
    }

    // Подбор товара из модального окна
    const btn = e.target.closest('.select-product-btn');
    if (btn) {
        
        // получаем текущую строку
        const row = btn.closest('tr');

        // получаем input количества
        const qtyInput = row.querySelector('input[name="item_quantity"]');

        // значение количества
        const quantity = parseInt(qtyInput.value) || 1;

        // возвращаем количество к исходной единичке
        qtyInput.value = 1;

        const product = {
            id: btn.dataset.id,
            name: btn.dataset.name,
            code: btn.dataset.code,
            price: parseFloat(btn.dataset.price),
            quantity: quantity
        };

        const tbody = document.querySelector('#order-items-container');

        // =========================
        // ИЩЕМ СУЩЕСТВУЮЩУЮ СТРОКУ
        // =========================
        const existingInput = tbody.querySelector(
            `input[name="item_product_id"][value="${product.id}"]`
        );

        // =====================================================
        // ЕСЛИ ТОВАР УЖЕ ЕСТЬ → УВЕЛИЧИВАЕМ КОЛИЧЕСТВО
        // =====================================================
        if (existingInput) {

            const row = existingInput.closest('.order-row');

            const qtyInput = row.querySelector('input[name="item_quantity"]');

            qtyInput.value = (parseInt(qtyInput.value) || 0) + product.quantity;

            // пересчет суммы строки
            const amountCell = row.querySelector('.order-unit-amount');

            const total = (parseInt(qtyInput.value) || 0) * product.price;

            amountCell.textContent = `${total.toFixed(2)}₽`;

            updateInvoiceTotals();

            // Сохраним ордер
            submitFormInBackground();

            return;
        }

        // =====================================================
        // ЕСЛИ НЕТ → СОЗДАЕМ НОВУЮ СТРОКУ
        // =====================================================
        const newRow = document.createElement('tr');

        newRow.className = 'order-row';

        newRow.innerHTML = `
            <td class="py-4">
                <small class="text-muted">${product.code}</small>
            </td>
            <td class="py-4">
                <div class="fw-bold"></div>
                <small class="text-muted">${product.name}</small>
                <input type="hidden" name="item_product_id" value="${product.id}">
            </td>

            <td>
                <div class="qty-control mx-auto">
                    <button type="button" class="qty-btn">-</button>
                    <input type="text" name="item_quantity" class="qty-input" value="${product.quantity}">
                    <button type="button" class="qty-btn">+</button>
                </div>
            </td>

            <td class="text-end fw-bold text-muted order-unit-price">
                ${product.price.toFixed(2)}₽
                <input type="hidden" name="item_price" value="${product.price}">
            </td>

            <td class="text-end fw-bold order-unit-amount">
                ${product.price.toFixed(2)}₽
            </td>

            <td class="text-end">
                <i class="bi bi-trash trash-btn"></i>
            </td>
        `;

        tbody.appendChild(newRow);

        updateInvoiceTotals();

        // Сохраним ордер
        submitFormInBackground();
            
    }
});

document.addEventListener('DOMContentLoaded', function() {
    
    const orderModal = new bootstrap.Modal(document.getElementById('orderModal'));
    const modalContent = document.getElementById('orderModalContent');

    // Делегирование: слушаем клики по кнопкам "Создать" или "Редактировать"
    document.addEventListener('click', function(e) {

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

document.addEventListener('submit', function(event) {
    
    // Проверяем, что событие пришло именно от нашей формы
    if (event.target && event.target.id === 'order-main-form') {
        const addressSelect = document.getElementById('address-select');
        const selectSelect = document.getElementById('client-select');
        const paymenttypeSelect = document.getElementById('paymenttype-select');

        let showAlert = false;

        console.log("сохраняем");

        if (!paymenttypeSelect || !paymenttypeSelect.value) {
            event.preventDefault(); // Останавливаем отправку
            paymenttypeSelect.classList.add('is-invalid');
            showAlert = true;
        }

        if (!selectSelect || !selectSelect.value || selectSelect.value === 'Выберите получателя') {
            event.preventDefault(); // Останавливаем отправку
            selectSelect.classList.add('is-invalid');
            showAlert = true;
        }

        if (!addressSelect || !addressSelect.value) {
            event.preventDefault(); // Останавливаем отправку
            addressSelect.classList.add('is-invalid');
            showAlert = true;
        }

        if (showAlert) {
            const toastLiveExample = document.getElementById('errorToast');
            const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toastLiveExample);
            toastBootstrap.show();
            return;
        }

        const confirmModal = new bootstrap.Modal(document.getElementById('confirmSaveModal'));

        // Если все ок, форма отправится и дальше уже будет обработана на сервере
        if (!event.detail || !event.detail.confirmed) {
         
            if (!confirmModal) return;

            event.preventDefault(); // Останавливаем отправку
            
            // Здесь можно добавить вашу проверку (например, выбран ли адрес)
            const address = document.getElementById('address-select').value;
            if (!address) {
                appendAlert('Сначала выберите адрес!', 'danger');
                return;
            }

            confirmModal.show(); // Показываем окно выбора
        }

        // 2. Обработка кнопки "Как черновик"
        document.getElementById('save-as-draft').addEventListener('click', function() {
            const finalStatusInput = document.getElementById('final-status');
            finalStatusInput.value = 'draft';
            submitForm(confirmModal);
        });

        // 3. Обработка кнопки "В обработку"
        document.getElementById('save-as-confirmed').addEventListener('click', function() {
            const finalStatusInput = document.getElementById('final-status');
            finalStatusInput.value = 'sent'; 
            submitForm(confirmModal);
        });

    }
});

document.addEventListener('click', function(e) {

    if (e.target.classList.contains('select-display-trigger')) {
        const container = e.target.closest('.custom-select-container');
        const dropdown = container.querySelector('.select-item-dropdown-menu');
        const resultList = container.querySelector('.results-list');
        
        // Закрываем другие открытые списки
        document.querySelectorAll('.select-dropdown-menu').forEach(d => {
            if (d !== dropdown) d.style.display = 'none';
        });

        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
        if (dropdown.style.display === 'block') {
            container.querySelector('#select-search').focus();
            renderInitialList(container);
        }
    }

    // Закрытие при клике вне компонента
    if (!e.target.closest('.custom-select-container')){
        document.querySelectorAll('.select-item-dropdown-menu').forEach(d => d.style.display = 'none');
    }
});

document.addEventListener('input', function(e) {

    if (e.target && e.target.id === 'select-search') {

        const container = e.target.closest('.custom-select-container');

        let timeout;
        const query = e.target.value.trim();
        const clientId = document.getElementById('client-select').value;
        
        if (query.length === 0) {
            renderInitialList(container);
            return;
        }

        clearTimeout(timeout);
        timeout = setTimeout(() => {
            // Замените URL на ваш эндпоинт Django
            fetch(`/api/products/search/?client_id=${clientId}&q=${query}`)
                .then(res => res.json())
                .then(data => renderItems(data, container))
                .catch(() => renderItems([], container));
        }, 300); // задержка 300мс
    }
});

document.addEventListener('DOMContentLoaded', function () {
    
    const previewModal = new bootstrap.Modal(document.getElementById('imagePreviewModal'));
    const modalImage = document.getElementById('modalFullImage');

    // Делегирование событий (работает даже если строки товаров добавляются динамически через JS!)
    document.addEventListener('click', function (e) {
        if (e.target.classList.contains('cp-zoom-trigger')) {
            const fullSizeSrc = e.target.getAttribute('data-full-src');
            
            if (fullSizeSrc) {
                modalImage.src = fullSizeSrc; // Устанавливаем тяжелую картинку
                previewModal.show();         // Показываем окно
            }
        }
    });
    
    // Очищаем src после закрытия модалки, чтобы при следующем открытии не моргало старое фото
    document.getElementById('imagePreviewModal').addEventListener('hidden.bs.modal', function () {
        modalImage.src = '';
    });
});
