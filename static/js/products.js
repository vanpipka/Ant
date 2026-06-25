// Конфигурация и состояние каталога номенклатуры
const ProductCatalog = {
    // Селекторы элементов UI
    el: {
        search: null,
        container: null,
        loader: null,
        endMessage: null
    },

    // Состояние пагинации и поиска
    state: {
        currentPage: 1,
        hasNextPage: true,
        isLoading: false,
        searchQuery: '',
        debounceTimer: null
    },

    // Инициализация модуля
    init() {
        this.el.search = document.getElementById('product-search-input');
        this.el.container = document.getElementById('product-list-results');
        this.el.loader = document.getElementById('pagination-loader');
        this.el.endMessage = document.getElementById('pagination-end');

        this.bindEvents();
    },

    // Привязка всех обработчиков событий
    bindEvents() {
        const offcanvas = document.getElementById('offcanvasRight');

        if (!offcanvas) {return;}

        // Открытие шторки
        offcanvas.addEventListener('shown.bs.offcanvas', () => {
            this.el.search.value = '';
            this.state.searchQuery = '';
            this.loadProducts(true); // Загрузка сбросит список на 1-ю страницу
        });

        // Скролл списка
        this.el.container.addEventListener('scroll', () => {
            const triggerPoint = this.el.container.scrollHeight - this.el.container.scrollTop - this.el.container.clientHeight;
            if (triggerPoint < 20 && !this.state.isLoading && this.state.hasNextPage) {
                this.loadProducts(false); // Подгрузка следующей страницы
            }
        });

        // Ввод в поиск (Debounce)
        this.el.search.addEventListener('input', (e) => {
            clearTimeout(this.state.debounceTimer);
            this.state.searchQuery = e.target.value.trim();

            this.state.debounceTimer = setTimeout(() => {
                this.loadProducts(true);
            }, 400);
        });
    },

    // МЕТОД 1: Загрузка данных (теперь вынесен в объект)
    async loadProducts(reset = false) {
        if (this.state.isLoading || (!this.state.hasNextPage && !reset)) return;

        const clientId = document.getElementById('client-select').value;

        this.state.isLoading = true;
        this.el.loader.style.display = 'block';
        this.el.endMessage.style.display = 'none';

        if (reset) {
            this.state.currentPage = 1;
            this.state.hasNextPage = true;
        }

        let url = `/api/products/search/?client_id=${clientId}&page=${this.state.currentPage}&page_size=20`;
        if (this.state.searchQuery) {
            url += `&q=${encodeURIComponent(this.state.searchQuery)}`;
        }

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Ошибка сети');
            
            const data = await response.json();

            if (reset) {
                this.el.container.innerHTML = '';
            }

            // Вызов метода рендеринга
            this.renderProducts(data.results);

            // Актуализируем пагинацию по ответу Django
            if (data.pagination.next_page) {
                this.state.currentPage = data.pagination.next_page;
                this.state.hasNextPage = true;
            } else {
                this.state.hasNextPage = false;
                if (this.el.container.children.length > 0) {
                    this.el.endMessage.style.display = 'block';
                }
            }

        } catch (error) {
            console.error('Ошибка:', error);
            this.el.container.innerHTML = `<div class="text-danger p-3">Не удалось загрузить товары</div>`;
        } finally {
            this.state.isLoading = false;
            this.el.loader.style.display = 'none';
        }
    },

    // МЕТОД 2: Рендеринг HTML (теперь вынесен в объект)
    renderProducts(products) {
        if (products.length === 0 && this.state.currentPage === 1) {
            this.el.container.innerHTML = `<div class="text-muted text-center p-3">Товары не найдены</div>`;
            return;
        }

        const mediaUrl = window.MEDIA_URL || '/media/';

        //const tbody = document.querySelector('#order-items-container');

        products.forEach(product => {

            let qty = 1;
            // =========================
            // ИЩЕМ СУЩЕСТВУЮЩУЮ СТРОКУ
            // =========================
            //const existingInput = tbody.querySelector(
            //    `input[name="item_product_id"][value="${product.product_id}"]`
            //);
            
            // =====================================================
            // ЕСЛИ ТОВАР УЖЕ ЕСТЬ → БЕРЕМ КОЛИЧЕСТВО
            // =====================================================
            //if (existingInput) {
            //    const row = existingInput.closest('.order-row');
            //    const qtyInput = row.querySelector('input[name="item_quantity"]');
            //    qty = qtyInput.value;
            //}
            
            const imageBlock = product.annotated_preview 
                ? `<img src="${mediaUrl}${product.annotated_preview}" 
                        data-full-src="${mediaUrl}${product.annotated_image}"
                        class="img-fluid rounded-3 cp-zoom-trigger" 
                        alt="${product.name}"
                        style="width: 100%; height: 100%; object-fit: cover; cursor: pointer;">`
                : `<div class="d-flex align-items-center justify-content-center h-100 w-100 rounded-3" 
                        style="background-color: #eaf7f7; color: #1abc9c;">
                        <i class="bi bi-box-seam fs-4"></i>
                   </div>`;

            const productHtml = `
            <tr>
                <td class="py-4">
                    <div class="d-flex align-items-center">
                        <div class="me-3 position-relative flex-shrink-0" style="width: 56px; height: 56px;">
                            ${imageBlock}
                        </div>

                        <div>
                            <h6 class="mb-1 fw-bold text-dark" style="font-size: 0.9rem;">
                                ${product.name}
                            </h6>
                            <small class="text-muted">
                                Арт: ${product.article} | Ед: ${product.unit}
                            </small>
                        </div>
                    </div>
                </td>
                <td>
                    <div class="qty-control mx-auto">
                        <button type="button" class="qty-btn">-</button>
                        <input type="text" name="item_quantity" class="qty-input" value="${qty}">
                        <button type="button" class="qty-btn">+</button>
                    </div>
                </td>
                        
                <!-- Цена -->
                <td class="text-end fw-bold text-muted ">
                    <div class="order-unit-price">
                        ${product.client_price} ₽
                    </div>
                    <input type="hidden" name="item_price" value="{{item.price}}">
                </td>
                          
                <!--<td class="text-end fw-bold order-unit-amount">₽</td>  -->                                       
                <td class="text-end">
                    <button
                        class="icon-link btn-new-invoice select-product-btn"
                        data-id="${product.product_id}"
                        data-name="${product.name}"
                        data-price="${product.client_price}"
                    >
                    <i class="bi bi-cart4 me-1"></i>
                        В заказ
                    </button>
                </td>
            </tr>
            `;

            this.el.container.insertAdjacentHTML('beforeend', productHtml);
        });
    }
};

function initProductCatalogSafe() {
    if (document.readyState === 'loading') {
        // Если DOM еще загружается, ждем его
        document.addEventListener('DOMContentLoaded', () => ProductCatalog.init());
    } else {
        // Если DOM уже готов (или скрипт загрузился позже), запускаем сразу!
        ProductCatalog.init();
    }
}

document.addEventListener('click', function(e) {
    if (e.target.closest('#add-item-btn-offcanvas')) {
        initProductCatalogSafe(); 
    }
});
