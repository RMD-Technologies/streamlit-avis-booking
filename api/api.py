import litserve as ls
from utils import batch_tokenize
from reach import Reach
from pathlib import Path
from sentence_transformers import SentenceTransformer
import os

MODELS_PATH = Path(__file__).parent / "models"

class TokenizeAPI(ls.LitAPI):

    def decode_request(self, request):
        return [[r['lang'], r['text']] for r in request['input']]

    def predict(self, request):
        return batch_tokenize(request)

    def encode_response(self, output):
        return {"output": output}

class WordEmbeddingsAPI(ls.LitAPI):
    
    def setup(self, device):
        self.MODELS = {
            'fr': Reach.load(MODELS_PATH / "w2v/fr.vec"),
            'en':Reach.load(MODELS_PATH / "w2v/en.vec")
        }
        
    def decode_request(self, request):
        return [[r['lang'], r['token']] for r in request['input']]

    def predict(self, request):
        outputs = []
        for lang, token in request:
            if lang not in self.MODELS:
                outputs.append({"error": f"Language '{lang}' not supported."})
            elif token not in self.MODELS[lang].items:
                outputs.append({"error": f"Token '{token}' not supported."})
            else:
                outputs.append({
                    "token": token,
                    "emb": self.MODELS[lang][token].tolist()  # Convert NumPy array to list for JSON
                })
        return outputs

    def encode_response(self, output):
        return {"output": output}

class SentenceEmbeddingsAPI(ls.LitAPI):

    def setup(self, device):
        self.MODEL = SentenceTransformer(str(MODELS_PATH / "sbert/multilingual-e5-TourCSE"), device=device)
        
    def decode_request(self, request):
        return request['input']

    def predict(self, request):
       return self.MODEL.encode(request, prompt="query: ", convert_to_numpy=True).tolist()

    def encode_response(self, output):
        return {"output": output}

if __name__ == "__main__":
    tokenize_api = TokenizeAPI(max_batch_size=1, api_path="/tokenizes")
    
    word_embeddings_api = WordEmbeddingsAPI(max_batch_size=1, api_path="/word_embeddings")

    sentence_embeddings_api = SentenceEmbeddingsAPI(max_batch_size=1, api_path="/sentence_embeddings")

    # Run Word Embeddings API
    ls.LitServer([tokenize_api, word_embeddings_api, sentence_embeddings_api]).run(port=8000)