import streamlit as st
import pandas as pd
from postgres import PostgresSingleton

db = PostgresSingleton()

DF_HOTELS = db.get_all_kalios()

def filter_hotel_to_select(is_id_booking=False, is_selected_by_default=True) -> pd.DataFrame:
    """
    Streamlit module to filter hotels for selection.
    Filters all columns except 'id', 'url', 'id_booking' and allows selecting hotels
    with NULL id_booking. Automatically adds date filters for columns containing 'date'.
    Displays filtered table in main page.
    """
    st.sidebar.header("🔎 Filtrage des hôtels")

    if 'selected_hotels' not in st.session_state:
        st.session_state.selected_hotels = set()
    

    filtered_df = DF_HOTELS.copy()

    # Filter by all columns except 'id', 'url', 'id_booking'
    filterable_columns = [col for col in filtered_df.columns if col not in ['id', 'url', 'id_booking', 'last_date_scrap']]
    
    for col in filterable_columns:
        # Si le type est datetime ou si le nom contient 'date'
      
        if filtered_df[col].dtype == object:
            search_val = st.sidebar.text_input(f"Recherche par {col}", key=col)
            if search_val:
                filtered_df = filtered_df[filtered_df[col].str.contains(search_val, case=False, na=False)]

    # Option to select hotels with id_booking = NULL
    if not is_id_booking:
        select_null_booking = st.sidebar.checkbox("Sélectionner uniquement les hôtels sans id_booking", value=False)
        if select_null_booking:
            filtered_df = filtered_df[filtered_df["id_booking"].isna() | (filtered_df["id_booking"] == "")]
    else:
        filtered_df = filtered_df[filtered_df["id_booking"].notna() & (filtered_df["id_booking"] != "")]

    # Multi-selection with checkboxes (display id - name - town)
    st.subheader("✅ Sélection des hôtels")
   
    options = [f"{idx} - {row['name']} - {row['town']}" for idx, row in filtered_df.iterrows()]
    
    select_all = st.sidebar.button("Tous les hôtels filtrés")
    default_selection = options if select_all else (options if is_selected_by_default else [])
    
   
    st.session_state.selected_hotels.update(default_selection)

    options =  list(set(options) | st.session_state.selected_hotels)

    options.sort(key=lambda x: (
        int(x.split(' - ')[0]),      # id comme entier
        x.split(' - ')[1].lower(),   # name, insensible à la casse
        x.split(' - ')[2].lower()    # town, insensible à la casse
    ))

    selected_options = st.sidebar.multiselect(
        "Sélectionnez les hôtels à traiter",
        options=options,
        default=list(st.session_state.selected_hotels)
    )


    # Keep only the selected rows
    if selected_options:
        filtered_df = DF_HOTELS.copy()
        selected_ids = [int(opt.split(" - ")[0]) for opt in selected_options]
        filtered_df = filtered_df[filtered_df.index.isin(selected_ids)]
    else:
        filtered_df = pd.DataFrame(columns=filtered_df.columns)

    # rename index by id_kalio
    filtered_df.index.name = 'id_kalio'

    # Display filtered table
    st.dataframe(filtered_df)

    return filtered_df
