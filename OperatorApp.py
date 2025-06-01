import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# --- MOCK DATA ---
operator_name = "Тестова Т. Т."
today = datetime.today().date()
dates = [today - timedelta(days=i) for i in range(7)][::-1]

# Пример данных об операциях
fraud_data = pd.DataFrame({
    "transaction_id": [101, 102, 103, 104],
    "client_id": [1001, 1002, 1003, 1004],
    "model_result": ["fraud", "fraud", "fraud", "fraud"],
    "operator_decision": ["", "", "", ""]
})

# Пример статистики по дням
fraud_stats = pd.DataFrame({
    "date": dates,
    "fraud_count": np.random.randint(3, 10, size=7),
})

operator_actions = pd.DataFrame({
    "date": [today],
    "to_check": [10],
    "checked": [7],
    "fraud_confirmed": [4]
})

# --- MAIN APP ---
st.set_page_config(page_title="Фрод-мониторинг", layout="wide")
st.title("Система мониторинга мошенничества")
st.markdown(f"### Оператор: {operator_name}")

st.subheader("Аналитическая таблица фродовых операций")
selected_row = st.data_editor(fraud_data, key="editor", use_container_width=True, num_rows="dynamic")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Динамика фродовых операций (по дням)")
    fig1 = px.bar(fraud_stats, x="date", y="fraud_count", labels={"date": "Дата", "fraud_count": "Количество"})
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Статистика действий оператора")
    row = operator_actions.iloc[0]
    fig2 = px.pie(values=[row['checked'], row['to_check'] - row['checked']],
                  names=["Проверено", "Осталось"],
                  title="Проверка операций")
    st.plotly_chart(fig2, use_container_width=True)
    st.metric("Процент подтвержденных фродов", f"{round(row['fraud_confirmed']/row['checked']*100, 1)}%")

# --- DETAILED PAGE ---
if st.session_state.get("editor"):
    chosen = st.session_state.editor.get("edited_rows")
    if chosen:
        detail_index = list(chosen.keys())[0]
        transaction = fraud_data.iloc[detail_index]

        st.markdown("---")
        st.subheader(f"Детализация транзакции ID: {transaction['transaction_id']}")

        st.markdown("**Информация о клиенте**")
        st.write({"Клиент ID": transaction['client_id'], "Регион": "ЮФО", "Пол": "Мужской", "Дата регистрации": "2023-04-10"})

        st.markdown("**Детали операции**")
        st.write({"Сумма": "12 500 ₽", "Время": "13:47", "Местоположение": "Краснодар"})

        st.markdown("**SHAP-анализ влияющих признаков**")
        shap_df = pd.DataFrame({
            "Признак": ["средняя сумма за неделю", "время суток", "расстояние до предыдущей операции"],
            "Влияние": [0.35, 0.28, 0.22]
        })
        fig3 = px.bar(shap_df, x="Влияние", y="Признак", orientation='h')
        st.plotly_chart(fig3, use_container_width=True)
