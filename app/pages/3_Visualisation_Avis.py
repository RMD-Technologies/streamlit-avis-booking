from utils import filter_hotel_to_select
from postgres.PostgresSingleton import PostgresSingleton

db = PostgresSingleton()

selected_hotels = filter_hotel_to_select(is_id_booking=True, is_selected_by_default=False)

indexes = selected_hotels.index.tolist()
print(indexes)

print(len(db.get_review_texts_by_ids(indexes)))

