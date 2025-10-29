import streamlit as st
import pandas as pd

def filter_hotel_to_select(df_hotels: pd.DataFrame, is_id_booking=False) -> pd.DataFrame:
    """
    Streamlit module to filter hotels for selection.
    Filters all columns except 'id', 'url', 'id_booking' and allows selecting hotels
    with NULL id_booking. Displays filtered table in main page.
    """
    st.sidebar.subheader("🔎 Filtrage des hôtels")

    filtered_df = df_hotels.copy()

    # Filter by all columns except 'id', 'url', 'id_booking'
    filterable_columns = [col for col in filtered_df.columns if col not in ['id', 'url', 'id_booking']]
    
    for col in filterable_columns:
        if filtered_df[col].dtype == object:
            search_val = st.sidebar.text_input(f"Recherche par {col}", key=col)
            if search_val:
                filtered_df = filtered_df[filtered_df[col].str.contains(search_val, case=False, na=False)]
        else:
            min_val, max_val = int(filtered_df[col].min()), int(filtered_df[col].max())
            selected_range = st.sidebar.slider(f"Filtrer par {col}", min_value=min_val, max_value=max_val,
                                               value=(min_val, max_val), key=col)
            filtered_df = filtered_df[(filtered_df[col] >= selected_range[0]) & (filtered_df[col] <= selected_range[1])]

    # Option to select hotels with id_booking = NULL
    if not is_id_booking:
        select_null_booking = st.sidebar.checkbox("Sélectionner uniquement les hôtels sans id_booking", value=False)
        if select_null_booking:
            filtered_df = filtered_df[filtered_df["id_booking"].isna() | (filtered_df["id_booking"] == "")]
    else:
        filtered_df = filtered_df[filtered_df["id_booking"].notna() & (filtered_df["id_booking"] != "")]

    # Multi-selection with checkboxes (display id - name - town)
    st.subheader("✅ Sélection finale des hôtels")
   
    options = [f"{idx} - {row['name']} - {row['town']}" for idx, row in filtered_df.iterrows()]
    selected_options = st.multiselect(
        "Sélectionnez les hôtels à traiter",
        options=options,
        default=options
    )

    # Keep only the selected rows
    if selected_options:
        selected_ids = [int(opt.split(" - ")[0]) for opt in selected_options]
        filtered_df = filtered_df[filtered_df.index.isin(selected_ids)]
    else:
        filtered_df = pd.DataFrame(columns=filtered_df.columns)

    # Display filtered table
    st.dataframe(filtered_df)

    return filtered_df
