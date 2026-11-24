from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import streamlit as st

import database as db

st.set_page_config(
    page_title="ChocoCren | Gestão de Delivery",
    page_icon="🍫",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.initialize_database()

st.markdown(
    """
    <style>
    :root {
        color-scheme: light;
        --cc-coral: #ff604e;
        --cc-dark: #171717;
        --cc-gray: #ffffff;
        --cc-background: #BFDDF3;
        --cc-surface: #ffffff;
        --cc-muted: #555555;
    }
    html, body, .stApp, [data-testid="stAppViewContainer"], section[data-testid="stMain"] {
        background-color: var(--cc-background) !important;
        color: var(--cc-dark) !important;
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp [data-testid="stMarkdownContainer"] p,
    .stApp [data-testid="stMarkdownContainer"] li,
    .stApp [data-testid="stMarkdownContainer"] strong,
    .stApp [data-testid="stMarkdownContainer"] em,
    .stApp [data-testid="stWidgetLabel"],
    .stApp [data-testid="stWidgetLabel"] p,
    .stApp [data-testid="stWidgetLabel"] label,
    .stApp [data-testid="stRadio"] label,
    .stApp [data-testid="stCheckbox"] label,
    .stApp [data-testid="stCaptionContainer"],
    .stApp [data-testid="stCaptionContainer"] p,
    .stApp [data-testid="stMetricLabel"],
    .stApp [data-testid="stMetricLabel"] *,
    .stApp [data-testid="stMetricValue"],
    .stApp [data-testid="stMetricValue"] * {
        color: var(--cc-dark) !important;
        -webkit-text-fill-color: var(--cc-dark) !important;
        opacity: 1 !important;
    }
    [data-testid="stSidebar"] {
        background: var(--cc-gray) !important;
        border-right: 1px solid #8d8d8d;
    }
    [data-testid="stSidebar"] * {
        color: #111111 !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        font-weight: 600;
    }
    [data-testid="stHeader"] {
        background: rgba(238, 238, 238, 0.96) !important;
    }
    .block-container {
        padding-top: 1.1rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }
    .cc-topbar {
        background: #aaaaaa;
        border-radius: 9px 9px 0 0;
        padding: 12px 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.1rem;
        color: #151515 !important;
    }
    .cc-brand, .cc-admin {
        color: #151515 !important;
    }
    .cc-brand {
        font-size: 1.08rem;
        font-weight: 800;
        letter-spacing: .02em;
    }
    .cc-admin {
        font-size: .82rem;
        font-weight: 600;
    }
    .cc-subtitle {
        color: #555555 !important;
        margin-top: -.65rem;
        margin-bottom: 1.1rem;
        font-size: .86rem;
    }
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border-radius: 13px;
        padding: 14px 16px;
        border: 1px solid #e1e1e1;
        min-height: 104px;
    }
    div[data-testid="stMetricLabel"] *,
    div[data-testid="stMetricValue"] * {
        color: #171717 !important;
        opacity: 1 !important;
    }
    .stApp input, .stApp textarea,
    .stApp [data-baseweb="input"] input,
    .stApp [data-baseweb="textarea"] textarea {
        color: #171717 !important;
        background-color: #ffffff !important;
        caret-color: #171717 !important;
        -webkit-text-fill-color: #171717 !important;
    }
    .stApp [data-baseweb="input"] > div,
    .stApp [data-baseweb="textarea"] {
        background-color: #ffffff !important;
        border-color: #b8b8b8 !important;
    }
    .stApp [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border-color: #b8b8b8 !important;
    }
    .stApp [data-baseweb="select"] *,
    .stApp [role="listbox"],
    .stApp [role="option"] {
        color: #171717 !important;
        -webkit-text-fill-color: #171717 !important;
    }
    .stApp [role="listbox"], .stApp [role="option"] {
        background-color: #ffffff !important;
    }
    .stApp input::placeholder, .stApp textarea::placeholder {
        color: #777777 !important;
        -webkit-text-fill-color: #777777 !important;
        opacity: 1 !important;
    }
    div.stButton > button, div.stFormSubmitButton > button {
        border-radius: 8px;
        font-weight: 650;
        min-height: 2.35rem;
        color: #171717 !important;
        background-color: #ffffff !important;
        border-color: #b8b8b8 !important;
    }
    div.stButton > button[kind="primary"],
    div.stFormSubmitButton > button[kind="primary"] {
        background: var(--cc-coral) !important;
        border-color: var(--cc-coral) !important;
        color: #ffffff !important;
    }
    div[data-testid="stForm"] {
        background: #ffffff !important;
        color: #171717 !important;
        border: 1px solid #e2e2e2;
        border-radius: 12px;
        padding: 16px;
    }
    div[data-testid="stExpander"] {
        background: #ffffff !important;
        color: #171717 !important;
        border: 1px solid #e2e2e2;
        border-radius: 10px;
    }
    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] summary * {
        color: #171717 !important;
    }
    .stApp [data-testid="stTabs"] button,
    .stApp [data-testid="stTabs"] button * {
        color: #333333 !important;
        -webkit-text-fill-color: #333333 !important;
    }
    .stApp [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--cc-coral) !important;
        -webkit-text-fill-color: var(--cc-coral) !important;
    }
    .stApp [data-testid="stDataFrame"] {
        color: #171717 !important;
    }
    .stApp [data-testid="stAlert"] {
        background-color: #edf2f7 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px;
    }
    .stApp [data-testid="stAlert"][kind="success"] {
        background-color: #e8f5ec !important;
        border-color: #b8dec3 !important;
    }
    .stApp [data-testid="stAlert"][kind="warning"] {
        background-color: #fff5db !important;
        border-color: #f0d58a !important;
    }
    .stApp [data-testid="stAlert"][kind="error"] {
        background-color: #fdeceb !important;
        border-color: #efb8b5 !important;
    }
    .stApp [data-testid="stAlert"][kind="info"] {
        background-color: #eaf1fb !important;
        border-color: #c6d7f0 !important;
    }
    .stApp [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p {
        color: #263238 !important;
        -webkit-text-fill-color: #263238 !important;
        opacity: 1 !important;
    }
    .stApp [data-testid="stVegaLiteChart"] {
        background: #ffffff !important;
        border-radius: 10px;
    }
    .cc-status {
        display: inline-block;
        background: #efefef;
        border: 1px solid #bbbbbb;
        color: #222222 !important;
        border-radius: 99px;
        padding: 2px 9px;
        font-size: .75rem;
    }
    .cc-note {
        color: #555555 !important;
        font-size: .85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def brl(cents: int) -> str:
    value = Decimal(int(cents)) / Decimal(100)
    return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def phone_digits(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if digits.startswith("55") and len(digits) in (12, 13):
        digits = digits[2:]
    return digits


def parse_percent(value: float) -> Decimal:
    try:
        result = Decimal(str(value)).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise db.RuleError("Percentual de desconto inválido.") from exc
    if not Decimal("0") <= result <= Decimal("100"):
        raise db.RuleError("O desconto deve estar entre 0% e 100%.")
    return result


def show_error(action):
    try:
        action()
    except db.RuleError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error("Ocorreu um erro inesperado ao salvar. Confira os dados e tente novamente.")
        print(f"Erro não tratado no ChocoCren: {type(exc).__name__}: {exc}")


def page_header(title: str, description: str, icon: str):
    st.markdown(f"## {icon}  {title}")
    st.markdown(f'<div class="cc-subtitle">{description}</div>', unsafe_allow_html=True)


def status_text(product: dict) -> str:
    if not product["active"]:
        return "Inativo"
    if product["stock"] == 0:
        return "Sem Estoque"
    if product["stock"] < product["min_stock"]:
        return "Estoque Baixo"
    return "Disponível"


def render_dashboard():
    page_header("Visão Geral", "Acompanhe os pedidos, a operação de entregas e os alertas da ChocoCren.", "📊")
    metrics = db.dashboard_metrics()
    cols = st.columns(4)
    cols[0].metric("Pedidos em Preparo", metrics["orders_preparing"])
    cols[1].metric("Entregas em Rota", metrics["orders_route"])
    cols[2].metric("Motoboys Disponíveis", metrics["couriers_available"])
    cols[3].metric("Produtos com Estoque Baixo", metrics["products_low"])

    left, right = st.columns([1.55, 1])
    with left:
        st.subheader("Valores registrados nos pedidos")
        st.caption("Resumo operacional dos pedidos não cancelados. Não representa controle contábil ou financeiro.")
        month_data = db.monthly_order_summary(11)
        if any(item["Valor dos pedidos (R$)"] > 0 for item in month_data):
            st.bar_chart(
                month_data,
                x="Mês",
                y="Valor dos pedidos (R$)",
                height=320,
                use_container_width=True,
            )
        else:
            with st.container(border=True):
                st.info("Os valores dos pedidos aparecerão aqui após o primeiro pedido.")
    with right:
        st.subheader("⚠️ Estoque crítico")
        critical = db.low_stock_products()
        if critical:
            st.error(f"{len(critical)} produto(s) abaixo do estoque mínimo.")
            st.dataframe(
                [{"Produto": p["name"], "Sabor": p["flavor"], "Peso": p["size"], "Estoque": p["stock"], "Mínimo": p["min_stock"]} for p in critical],
                hide_index=True, use_container_width=True,
            )
        else:
            st.success("Nenhum produto abaixo do estoque mínimo.")

    st.divider()
    left, right = st.columns([1.55, 1])
    with left:
        st.subheader("Fila de pedidos ativos")
        active_orders = db.list_orders("Em Preparo") + db.list_orders("Saiu para Entrega")
        active_orders.sort(key=lambda item: item["id"], reverse=True)
        if active_orders:
            st.dataframe(
                [{"Pedido": o["code"], "Cliente": o["customer_name"], "Status": o["status"],
                  "Total": brl(o["total_cents"]), "Motoboy": o["motoboy_name"] or "Não atribuído"} for o in active_orders[:12]],
                hide_index=True, use_container_width=True,
            )
        else:
            st.info("Não há pedidos ativos no momento.")
    with right:
        st.subheader("Resumo da frota")
        available = [m for m in db.list_motoboys(include_inactive=False) if m["status"] == "Disponível"]
        st.metric("Entregadores livres", len(available))
        if available:
            for motoboy in available[:6]:
                st.write(f"🛵 **{motoboy['name']}** · {motoboy['plate']}")
        else:
            st.caption("Nenhum entregador disponível para novos despachos.")


def render_products():
    page_header("Gestão dos Produtos", "Cadastre, consulte, edite e gerencie os produtos e o estoque da ChocoCren.", "🍫")
    products = db.list_products(include_inactive=True)
    active = [p for p in products if p["active"]]
    in_stock = sum(1 for p in active if p["stock"] > 0 and p["stock"] >= p["min_stock"])
    low = sum(1 for p in active if 0 < p["stock"] < p["min_stock"])
    out = sum(1 for p in active if p["stock"] == 0)
    c = st.columns(4)
    c[0].metric("Total de produtos ativos", len(active))
    c[1].metric("Em estoque", in_stock)
    c[2].metric("Estoque baixo", low)
    c[3].metric("Sem estoque", out)

    with st.expander("🔎 Pesquisar e filtrar catálogo", expanded=True):
        f1, f2, f3 = st.columns([2, 1, 1])
        search = f1.text_input("Pesquisar por nome, sabor ou SKU", key="prod_search")
        category = f2.selectbox("Categoria", ["Todas"] + list(db.PRODUCT_CATEGORIES), key="prod_category_filter")
        availability = f3.selectbox("Disponibilidade", ["Todas", "Disponível", "Estoque Baixo", "Sem Estoque", "Inativo"], key="prod_availability_filter")
    filtered = products
    if search.strip():
        q = search.casefold()
        filtered = [p for p in filtered if q in p["name"].casefold() or q in p["flavor"].casefold() or q in p["sku"].casefold()]
    if category != "Todas":
        filtered = [p for p in filtered if p["category"] == category]
    if availability != "Todas":
        filtered = [p for p in filtered if status_text(p) == availability]
    if filtered:
        st.dataframe(
            [{"Código": p["sku"], "Produto": p["name"], "Tipo": p["category"], "Sabor": p["flavor"],
              "Peso": p["size"], "Preço unitário": brl(p["price_cents"]), "Estoque": p["stock"],
              "Estoque mínimo": p["min_stock"], "Status": status_text(p)} for p in filtered],
            hide_index=True, use_container_width=True,
        )
    else:
        st.info("Nenhum produto encontrado com os filtros selecionados.")

    st.divider()
    create_tab, edit_tab = st.tabs(["➕ Cadastrar produto", "✏️ Editar / gerenciar produto"])
    with create_tab:
        st.subheader("Novo produto")
        with st.form("new_product_form", clear_on_submit=True):
            a, b = st.columns(2)
            name = a.text_input("Nome do produto", placeholder="Ex.: Barra de Chocolate ao Leite")
            category_new = b.selectbox("Tipo / categoria", db.PRODUCT_CATEGORIES)
            flavor, size = st.columns(2)
            flavor_new = flavor.text_input("Sabor", placeholder="Ex.: Chocolate ao leite")
            size_new = size.text_input("Tamanho / peso", placeholder="Ex.: 100g")
            price_col, stock_col, min_col = st.columns(3)
            price_new = price_col.number_input("Preço unitário (R$)", min_value=0.01, max_value=1_000_000.0, value=8.50, step=0.50, format="%.2f")
            stock_new = stock_col.number_input("Quantidade inicial", min_value=0, max_value=1_000_000, value=0, step=1)
            min_new = min_col.number_input("Estoque mínimo", min_value=0, max_value=1_000_000, value=db.DEFAULT_MIN_STOCK, step=1)
            submitted = st.form_submit_button("Salvar produto", type="primary", use_container_width=True)
        if submitted:
            try:
                code = db.create_product(name, category_new, flavor_new, size_new, db.money_to_cents(price_new), int(stock_new), int(min_new))
                st.success(f"Produto cadastrado com sucesso. Código: {code}.")
                st.rerun()
            except db.RuleError as exc:
                st.error(str(exc))

    with edit_tab:
        editable = products
        if not editable:
            st.info("Cadastre o primeiro produto para habilitar a edição.")
        else:
            options = {f"{p['sku']} · {p['name']} ({'Ativo' if p['active'] else 'Inativo'})": p["id"] for p in editable}
            selected_label = st.selectbox("Selecione o produto", list(options), key="edit_product_selector")
            selected_id = options[selected_label]
            p = db.get_product(selected_id)
            with st.form("edit_product_form"):
                a, b = st.columns(2)
                name_edit = a.text_input("Nome", value=p["name"])
                category_edit = b.selectbox("Tipo / categoria", db.PRODUCT_CATEGORIES, index=db.PRODUCT_CATEGORIES.index(p["category"]))
                x, y = st.columns(2)
                flavor_edit = x.text_input("Sabor", value=p["flavor"])
                size_edit = y.text_input("Tamanho / peso", value=p["size"])
                x, y, z = st.columns(3)
                price_edit = x.number_input("Preço unitário (R$)", min_value=0.01, max_value=1_000_000.0, value=p["price_cents"] / 100, step=0.50, format="%.2f")
                stock_edit = y.number_input("Estoque atual", min_value=0, max_value=1_000_000, value=int(p["stock"]), step=1)
                min_edit = z.number_input("Estoque mínimo", min_value=0, max_value=1_000_000, value=int(p["min_stock"]), step=1)
                save_edit = st.form_submit_button("Salvar alterações", type="primary", use_container_width=True)
            if save_edit:
                try:
                    db.update_product(selected_id, name_edit, category_edit, flavor_edit, size_edit,
                                      db.money_to_cents(price_edit), int(stock_edit), int(min_edit))
                    st.success("Produto atualizado. Ajustes no estoque foram registrados no histórico.")
                    st.rerun()
                except db.RuleError as exc:
                    st.error(str(exc))
            action_cols = st.columns(3)
            if p["active"]:
                if action_cols[0].button("Inativar produto", key=f"deactivate_product_{selected_id}"):
                    try:
                        db.set_product_active(selected_id, False)
                        st.success("Produto inativado e removido das novas encomendas.")
                        st.rerun()
                    except db.RuleError as exc:
                        st.error(str(exc))
            else:
                if action_cols[0].button("Reativar produto", key=f"activate_product_{selected_id}"):
                    try:
                        db.set_product_active(selected_id, True)
                        st.success("Produto reativado.")
                        st.rerun()
                    except db.RuleError as exc:
                        st.error(str(exc))
            order_history = db.product_has_order_history(selected_id)
            if not order_history:
                if action_cols[1].button("Excluir definitivamente", key=f"delete_product_{selected_id}"):
                    try:
                        db.delete_product_if_unused(selected_id)
                        st.success("Produto excluído.")
                        st.rerun()
                    except db.RuleError as exc:
                        st.error(str(exc))
            else:
                action_cols[1].button("Excluir bloqueado", disabled=True, key=f"delete_product_blocked_{selected_id}")
                st.caption("Este produto tem histórico de pedidos; use Inativar para preservar a integridade dos registros.")
            with st.expander("Histórico recente de movimentações de estoque"):
                movements = db.get_stock_movements(selected_id)
                if movements:
                    st.dataframe([{"Data": m["created_at"], "Movimento": m["movement_type"], "Variação": m["quantity_change"], "Observação": m["note"]} for m in movements], hide_index=True, use_container_width=True)
                else:
                    st.caption("Ainda não há movimentações registradas.")


def render_motoboy_management():
    page_header("Gestão dos Motoboys", "Cadastre, consulte e controle a disponibilidade operacional dos entregadores.", "🛵")
    motoboys = db.list_motoboys(include_inactive=True)
    active = [m for m in motoboys if m["active"]]
    stats = [
        len(active),
        sum(1 for m in active if m["status"] == "Disponível"),
        sum(1 for m in active if m["status"] == "Indisponível"),
        sum(1 for m in active if m["status"] == "Em Manutenção"),
    ]
    c = st.columns(4)
    c[0].metric("Total de motoboys ativos", stats[0])
    c[1].metric("Disponíveis", stats[1])
    c[2].metric("Indisponíveis", stats[2])
    c[3].metric("Em manutenção", stats[3])

    search_col, status_col = st.columns([2, 1])
    search = search_col.text_input("Pesquisar por nome, telefone ou placa", key="courier_search")
    filter_status = status_col.selectbox("Filtrar status", ["Todos"] + list(db.COURIER_STATUSES), key="courier_filter")
    visible = motoboys
    if search.strip():
        q = search.casefold()
        visible = [m for m in visible if q in m["name"].casefold() or q in m["phone"] or q in m["plate"].casefold()]
    if filter_status != "Todos":
        visible = [m for m in visible if m["status"] == filter_status]
    if visible:
        st.dataframe(
            [{"ID": m["code"], "Nome": m["name"], "Telefone": m["phone"], "Placa": m["plate"],
              "Status": m["status"], "Situação do cadastro": "Ativo" if m["active"] else "Inativo"} for m in visible],
            hide_index=True, use_container_width=True,
        )
    else:
        st.info("Nenhum entregador encontrado.")

    st.divider()
    create_tab, edit_tab = st.tabs(["➕ Novo motoboy", "✏️ Editar / gerenciar frota"])
    with create_tab:
        with st.form("new_courier_form", clear_on_submit=True):
            x, y = st.columns(2)
            courier_name = x.text_input("Nome completo")
            courier_phone_input = y.text_input("Telefone", placeholder="11988887777")
            x, y = st.columns(2)
            courier_plate = x.text_input("Placa do veículo", placeholder="ABC1D23").upper()
            courier_status = y.selectbox("Status inicial", ["Disponível", "Indisponível"])
            observations = st.text_area("Observações", placeholder="Regiões atendidas, observações operacionais (opcional).", max_chars=300)
            create_courier = st.form_submit_button("Cadastrar motoboy", type="primary", use_container_width=True)
        if create_courier:
            try:
                code = db.create_motoboy(courier_name, phone_digits(courier_phone_input), courier_plate, courier_status, observations)
                st.success(f"Entregador cadastrado. Código: {code}.")
                st.rerun()
            except db.RuleError as exc:
                st.error(str(exc))

    with edit_tab:
        if not motoboys:
            st.info("Cadastre um entregador para habilitar a edição.")
        else:
            options = {f"{m['code']} · {m['name']} ({'Ativo' if m['active'] else 'Inativo'})": m["id"] for m in motoboys}
            selected_label = st.selectbox("Selecione o entregador", list(options), key="edit_courier_selector")
            selected_id = options[selected_label]
            m = db.get_motoboy(selected_id)
            status_options = ["Disponível", "Indisponível", "Em Manutenção"]
            if m["status"] == "Em Entrega":
                status_options.append("Em Entrega")
            with st.form("edit_courier_form"):
                x, y = st.columns(2)
                name_edit = x.text_input("Nome completo", value=m["name"])
                phone_edit_input = y.text_input("Telefone", value=m["phone"])
                x, y = st.columns(2)
                plate_edit = x.text_input("Placa", value=m["plate"])
                status_edit = y.selectbox("Status", status_options, index=status_options.index(m["status"]))
                obs_edit = st.text_area("Observações", value=m["observations"], max_chars=300)
                save_courier = st.form_submit_button("Salvar alterações", type="primary", use_container_width=True)
            if save_courier:
                try:
                    db.update_motoboy(selected_id, name_edit, phone_digits(phone_edit_input), plate_edit, status_edit, obs_edit)
                    st.success("Cadastro do entregador atualizado.")
                    st.rerun()
                except db.RuleError as exc:
                    st.error(str(exc))
            x, y = st.columns(2)
            if m["active"]:
                if x.button("Inativar entregador", key=f"deactivate_courier_{selected_id}"):
                    try:
                        db.set_motoboy_active(selected_id, False)
                        st.success("Entregador inativado.")
                        st.rerun()
                    except db.RuleError as exc:
                        st.error(str(exc))
            else:
                if x.button("Reativar entregador", key=f"activate_courier_{selected_id}"):
                    db.set_motoboy_active(selected_id, True)
                    st.success("Entregador reativado.")
                    st.rerun()
            has_history = db.motoboy_has_order_history(selected_id)
            if not has_history:
                if y.button("Excluir definitivamente", key=f"delete_courier_{selected_id}"):
                    try:
                        db.delete_motoboy_if_unused(selected_id)
                        st.success("Entregador excluído.")
                        st.rerun()
                    except db.RuleError as exc:
                        st.error(str(exc))
            else:
                y.button("Exclusão bloqueada", disabled=True, key=f"delete_courier_blocked_{selected_id}")
                st.caption("Este entregador possui histórico de pedidos; use Inativar para preservar os registros.")



def render_orders():
    page_header("Gestão de Pedidos", "Registre encomendas, acompanhe o andamento e cancele pedidos com estorno automático do estoque.", "🧾")
    st.subheader("Nova encomenda")
    products = [p for p in db.list_products(include_inactive=False) if p["stock"] > 0]
    if "order_cart" not in st.session_state:
        st.session_state.order_cart = {}
    if "order_form_version" not in st.session_state:
        st.session_state.order_form_version = 0
    form_version = st.session_state.order_form_version

    with st.container(border=True):
        a, b = st.columns(2)
        customer = a.text_input("Nome do cliente", key=f"order_customer_{form_version}")
        phone_input = b.text_input("Telefone do cliente", key=f"order_phone_{form_version}", placeholder="11988887777")
        address = st.text_input("Endereço de entrega", key=f"order_address_{form_version}", placeholder="Rua, número, bairro, complemento e referência")
        st.markdown("**Produtos da encomenda**")
        if products:
            product_map = {f"{p['name']} · {p['flavor']} · {p['size']} — {brl(p['price_cents'])} (estoque: {p['stock']})": p for p in products}
            with st.form("add_cart_item_form"):
                x, y = st.columns([3, 1])
                chosen_label = x.selectbox("Produto", list(product_map))
                quantity = y.number_input("Quantidade", min_value=1, max_value=1000, value=1, step=1)
                add_item = st.form_submit_button("Adicionar ao pedido")
            if add_item:
                chosen = product_map[chosen_label]
                current = int(st.session_state.order_cart.get(chosen["id"], 0))
                proposed = current + int(quantity)
                if proposed > chosen["stock"]:
                    st.error(f"Estoque insuficiente. Disponível: {chosen['stock']}; já no carrinho: {current}.")
                else:
                    st.session_state.order_cart[chosen["id"]] = proposed
                    st.rerun()
        else:
            st.warning("Não há produtos ativos com estoque disponível. Cadastre ou reponha produtos antes de registrar pedidos.")

        cart = st.session_state.order_cart
        subtotal_cents = 0
        if cart:
            st.markdown("**Itens adicionados**")
            current_products = {p["id"]: p for p in db.list_products(include_inactive=True)}
            for product_id, qty in list(cart.items()):
                p = current_products.get(product_id)
                if not p or not p["active"]:
                    st.warning("Um produto do carrinho foi inativado. Remova-o antes de finalizar.")
                    continue
                line = int(p["price_cents"]) * int(qty)
                subtotal_cents += line
                col1, col2, col3, col4 = st.columns([3, 1, 1, 0.6])
                col1.write(f"**{p['name']}** · {p['size']}")
                col2.write(f"Qtd.: {qty}")
                col3.write(brl(line))
                if col4.button("✕", key=f"remove_cart_{product_id}"):
                    del st.session_state.order_cart[product_id]
                    st.rerun()
        else:
            st.info("O carrinho está vazio. Adicione um ou mais produtos.")

        st.divider()
        x, y, z = st.columns(3)
        discount = x.number_input("Desconto (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5, format="%.2f", key=f"order_discount_{form_version}")
        delivery_fee = y.number_input("Taxa de entrega (R$)", min_value=0.0, max_value=1_000_000.0, value=0.0, step=1.0, format="%.2f", key=f"order_delivery_fee_{form_version}")
        service_fee = z.number_input("Taxa de serviço (R$)", min_value=0.0, max_value=1_000_000.0, value=0.0, step=0.5, format="%.2f", key=f"order_service_fee_{form_version}")
        try:
            discount_decimal = parse_percent(discount)
            discount_cents = int((Decimal(subtotal_cents) * discount_decimal / Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            total_cents = subtotal_cents - discount_cents + db.money_to_cents(delivery_fee) + db.money_to_cents(service_fee)
            sum1, sum2, sum3 = st.columns(3)
            sum1.metric("Subtotal", brl(subtotal_cents))
            sum2.metric("Desconto", brl(discount_cents))
            sum3.metric("Total estimado", brl(total_cents))
        except db.RuleError as exc:
            st.error(str(exc))
            total_cents = 0

        if st.button("Finalizar pedido", type="primary", use_container_width=True, disabled=not cart):
            try:
                order_code = db.create_order(
                    customer, phone_digits(phone_input), address,
                    [(int(pid), int(qty)) for pid, qty in cart.items()],
                    parse_percent(discount), db.money_to_cents(delivery_fee), db.money_to_cents(service_fee),
                )
                st.session_state.order_cart = {}
                st.session_state.order_form_version += 1
                st.success(f"Pedido {order_code} registrado. Estoques baixados automaticamente.")
                st.rerun()
            except db.RuleError as exc:
                st.error(str(exc))

    st.divider()
    st.subheader("Meus pedidos")
    filter_col, search_col = st.columns([1, 2])
    status_filter = filter_col.selectbox("Filtrar por status", ["Todos"] + list(db.ORDER_STATUSES), key="orders_status_filter")
    search = search_col.text_input("Buscar por nº do pedido, cliente ou produto", key="orders_search")
    orders = db.list_orders(status_filter, search)
    if not orders:
        st.info("Nenhum pedido encontrado.")
    for order in orders:
        with st.expander(f"{order['code']} · {order['customer_name']} · {order['status']} · {brl(order['total_cents'])}"):
            detail = db.get_order(order["id"])
            st.write(f"**Telefone:** {detail['customer_phone']}  |  **Endereço:** {detail['delivery_address']}")
            st.dataframe(
                [{"Produto": i["product_name"], "Tipo": i["category"], "Sabor": i["flavor"], "Peso": i["size"],
                  "Quantidade": i["quantity"], "Preço unitário": brl(i["unit_price_cents"]), "Subtotal": brl(i["subtotal_cents"])} for i in detail["items"]],
                hide_index=True, use_container_width=True,
            )
            st.write(f"**Subtotal:** {brl(detail['subtotal_cents'])} · **Desconto:** {detail['discount_percent']}% · **Total:** {brl(detail['total_cents'])}")
            if detail["motoboy_name"]:
                st.write(f"**Motoboy:** {detail['motoboy_name']} ({detail['motoboy_code']})")
            if detail["status"] == "Em Preparo":
                couriers = db.available_motoboys()
                if couriers:
                    courier_opts = {f"{m['name']} · {m['plate']}": m["id"] for m in couriers}
                    c1, c2 = st.columns([2, 1])
                    courier_label = c1.selectbox("Motoboy disponível", list(courier_opts), key=f"assign_order_courier_{order['id']}")
                    if c2.button("Despachar pedido", key=f"assign_order_{order['id']}", type="primary"):
                        try:
                            db.assign_order_to_motoboy(order["id"], courier_opts[courier_label])
                            st.success("Pedido saiu para entrega e motoboy passou para Em Entrega.")
                            st.rerun()
                        except db.RuleError as exc:
                            st.error(str(exc))
                else:
                    st.caption("Não há motoboys disponíveis para despacho.")
            elif detail["status"] == "Saiu para Entrega":
                if st.button("Confirmar entrega", key=f"deliver_order_{order['id']}", type="primary"):
                    try:
                        db.complete_delivery(order["id"])
                        st.success("Entrega concluída. O motoboy voltou para Disponível.")
                        st.rerun()
                    except db.RuleError as exc:
                        st.error(str(exc))
            if detail["status"] in ("Em Preparo", "Saiu para Entrega"):
                with st.form(f"cancel_order_form_{order['id']}"):
                    reason = st.text_input("Motivo do cancelamento (obrigatório)")
                    cancel = st.form_submit_button("Cancelar pedido e estornar estoque")
                if cancel:
                    try:
                        db.cancel_order(order["id"], reason)
                        st.success("Pedido cancelado. Quantidades devolvidas ao estoque automaticamente.")
                        st.rerun()
                    except db.RuleError as exc:
                        st.error(str(exc))
            elif detail["status"] == "Cancelado":
                st.warning(f"Cancelado: {detail['cancellation_reason']}")


def render_deliveries():
    page_header("Entregas e Frota", "Gerencie os motoboys, despache pedidos e confirme a conclusão das entregas.", "🛵")
    orders_preparing = db.list_orders("Em Preparo")
    orders_route = db.list_orders("Saiu para Entrega")
    motoboys = db.list_motoboys(include_inactive=False)
    c = st.columns(4)
    c[0].metric("Pedidos aguardando despacho", len(orders_preparing))
    c[1].metric("Pedidos em rota", len(orders_route))
    c[2].metric("Motoboys disponíveis", len([m for m in motoboys if m["status"] == "Disponível"]))
    c[3].metric("Motoboys em entrega", len([m for m in motoboys if m["status"] == "Em Entrega"]))

    dispatch_tab, route_tab, fleet_tab = st.tabs(["🚀 Despachar pedidos", "📦 Entregas em rota", "🛵 Frota"])
    with dispatch_tab:
        st.subheader("Atribuir pedido a um motoboy")
        available = db.available_motoboys()
        if not orders_preparing:
            st.info("Não há pedidos aguardando despacho.")
        elif not available:
            st.warning("Não há motoboys disponíveis. Cadastre ou altere a disponibilidade da frota.")
        else:
            order_options = {f"{o['code']} · {o['customer_name']} · {brl(o['total_cents'])}": o["id"] for o in orders_preparing}
            courier_options = {f"{m['name']} · {m['plate']}": m["id"] for m in available}
            with st.form("dispatch_form"):
                selected_order = st.selectbox("Pedido em preparo", list(order_options))
                selected_courier = st.selectbox("Motoboy disponível", list(courier_options))
                dispatch = st.form_submit_button("Atribuir e despachar", type="primary", use_container_width=True)
            if dispatch:
                try:
                    db.assign_order_to_motoboy(order_options[selected_order], courier_options[selected_courier])
                    st.success("Pedido despachado. Status do pedido: Saiu para Entrega; status do motoboy: Em Entrega.")
                    st.rerun()
                except db.RuleError as exc:
                    st.error(str(exc))

    with route_tab:
        st.subheader("Pedidos em rota")
        if orders_route:
            for order in orders_route:
                x, y = st.columns([3, 1])
                x.write(f"**{order['code']} · {order['customer_name']}**  \nMotoboy: {order['motoboy_name'] or 'Não identificado'} · {order['delivery_address']}")
                if y.button("Confirmar entrega", key=f"route_delivered_{order['id']}", type="primary"):
                    try:
                        db.complete_delivery(order["id"])
                        st.success(f"Pedido {order['code']} entregue. Motoboy liberado.")
                        st.rerun()
                    except db.RuleError as exc:
                        st.error(str(exc))
                st.divider()
        else:
            st.info("Nenhum pedido está em rota neste momento.")

    with fleet_tab:
        render_motoboy_management()


st.markdown(
    '<div class="cc-topbar"><div class="cc-brand">🍫 CHOCOCREN <span style="font-weight:400;font-size:.78rem">· Gestão de Delivery</span></div><div class="cc-admin">● Administrador</div></div>',
    unsafe_allow_html=True,
)
with st.sidebar:
    st.markdown("# 🍫 ChocoCren")
    st.caption("Sistema interno de gestão")
    st.divider()
    page = st.radio(
        "Navegação",
        ["Visão Geral", "Produtos", "Pedidos", "Entregas"],
        format_func=lambda x: {"Visão Geral": "📊  Visão Geral", "Produtos": "🍫  Produtos", "Pedidos": "🧾  Pedidos", "Entregas": "🛵  Entregas"}[x],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Acesso pela rede local · Porta 8501")

if page == "Visão Geral":
    render_dashboard()
elif page == "Produtos":
    render_products()
elif page == "Pedidos":
    render_orders()
else:
    render_deliveries()
