---
tags:
- sentence-transformers
- sentence-similarity
- feature-extraction
- dense
- generated_from_trainer
- dataset_size:300000
- loss:GISTEmbedLoss
base_model: intfloat/multilingual-e5-small
widget:
- source_sentence: 'query: literies trop fermes et oreillers pas assez gros donc mal
    aux cervicales.'
  sentences:
  - 'query: non respectueux.'
  - 'query: la literie est correcte.'
  - 'query: bruits et difficultés à régler l’eau de la douche (trop chaude)'
- source_sentence: 'query: la qualité des équipements : literie, salle de bain, petit
    déjeuner, propreté, le personnel'
  sentences:
  - 'query: le confort le calme le petit déjeuner'
  - 'query: je n’ai pas aimé la literie pas confortable du tout évier de la salle
    de bain bouché et baignoire également la chambre n’était pas confortable !'
  - 'query: bon rapport qualité prix et emplacement'
- source_sentence: 'query: petit déjeuner classique et bon, servi dans une jolie salle
    par un personnel attentif !'
  sentences:
  - 'query: déjeuner excellent avec une machine qui pressse les oranges pour le jus
    d’orange du matin.'
  - 'query: télé seulement 2 chaînes ( 2 et 3)'
  - 'query: le personnel est attentif, soigné et dévoué'
- source_sentence: 'query: la taille des chambres- un peu petite'
  sentences:
  - 'query: le petit déjeuner est maigre, peut mieux faire avec des produits simples.'
  - 'query: petit déjeuner excellent .très bon accueil ,les lieux sont bien tenus
    et les chambres très kleen !'
  - 'query: nous vous avons testé exprès.'
- source_sentence: 'query: chambre spacieuse comme dans la description à un prix correct.'
  sentences:
  - 'query: la douche en cabine plastique le lavabo à côté du lit'
  - 'query: hôtel bien placé en centre ville'
  - 'query: petit déjeuner impeccable'
pipeline_tag: sentence-similarity
library_name: sentence-transformers
metrics:
- pearson_cosine
- spearman_cosine
model-index:
- name: SentenceTransformer based on intfloat/multilingual-e5-small
  results:
  - task:
      type: semantic-similarity
      name: Semantic Similarity
    dataset:
      name: sgts
      type: sgts
    metrics:
    - type: pearson_cosine
      value: 0.42472518870062154
      name: Pearson Cosine
    - type: spearman_cosine
      value: 0.42761737137050815
      name: Spearman Cosine
---

# SentenceTransformer based on intfloat/multilingual-e5-small

This is a [sentence-transformers](https://www.SBERT.net) model finetuned from [intfloat/multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small). It maps sentences & paragraphs to a 384-dimensional dense vector space and can be used for semantic textual similarity, semantic search, paraphrase mining, text classification, clustering, and more.

## Model Details

### Model Description
- **Model Type:** Sentence Transformer
- **Base model:** [intfloat/multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small) <!-- at revision c007d7ef6fd86656326059b28395a7a03a7c5846 -->
- **Maximum Sequence Length:** 512 tokens
- **Output Dimensionality:** 384 dimensions
- **Similarity Function:** Cosine Similarity
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Documentation:** [Sentence Transformers Documentation](https://sbert.net)
- **Repository:** [Sentence Transformers on GitHub](https://github.com/UKPLab/sentence-transformers)
- **Hugging Face:** [Sentence Transformers on Hugging Face](https://huggingface.co/models?library=sentence-transformers)

### Full Model Architecture

```
SentenceTransformer(
  (0): Transformer({'max_seq_length': 512, 'do_lower_case': False, 'architecture': 'BertModel'})
  (1): Pooling({'word_embedding_dimension': 384, 'pooling_mode_cls_token': False, 'pooling_mode_mean_tokens': True, 'pooling_mode_max_tokens': False, 'pooling_mode_mean_sqrt_len_tokens': False, 'pooling_mode_weightedmean_tokens': False, 'pooling_mode_lasttoken': False, 'include_prompt': True})
  (2): Normalize()
)
```

## Usage

### Direct Usage (Sentence Transformers)

First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```

Then you can load this model and run inference.
```python
from sentence_transformers import SentenceTransformer

# Download from the 🤗 Hub
model = SentenceTransformer("sentence_transformers_model_id")
# Run inference
sentences = [
    'query: chambre spacieuse comme dans la description à un prix correct.',
    'query: petit déjeuner impeccable',
    'query: hôtel bien placé en centre ville',
]
embeddings = model.encode(sentences)
print(embeddings.shape)
# [3, 384]

# Get the similarity scores for the embeddings
similarities = model.similarity(embeddings, embeddings)
print(similarities)
# tensor([[1.0000, 0.5427, 0.5805],
#         [0.5427, 1.0000, 0.5641],
#         [0.5805, 0.5641, 1.0000]])
```

<!--
### Direct Usage (Transformers)

<details><summary>Click to see the direct usage in Transformers</summary>

</details>
-->

<!--
### Downstream Usage (Sentence Transformers)

You can finetune this model on your own dataset.

<details><summary>Click to expand</summary>

</details>
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

## Evaluation

### Metrics

#### Semantic Similarity

* Dataset: `sgts`
* Evaluated with [<code>EmbeddingSimilarityEvaluator</code>](https://sbert.net/docs/package_reference/sentence_transformer/evaluation.html#sentence_transformers.evaluation.EmbeddingSimilarityEvaluator)

| Metric              | Value      |
|:--------------------|:-----------|
| pearson_cosine      | 0.4247     |
| **spearman_cosine** | **0.4276** |

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Dataset

#### Unnamed Dataset

* Size: 300,000 training samples
* Columns: <code>sentence_1</code>, <code>sentence_2</code>, and <code>label</code>
* Approximate statistics based on the first 1000 samples:
  |         | sentence_1                                                                         | sentence_2                                                                         | label                        |
  |:--------|:-----------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------|:-----------------------------|
  | type    | string                                                                             | string                                                                             | int                          |
  | details | <ul><li>min: 6 tokens</li><li>mean: 21.17 tokens</li><li>max: 106 tokens</li></ul> | <ul><li>min: 6 tokens</li><li>mean: 22.13 tokens</li><li>max: 252 tokens</li></ul> | <ul><li>1: 100.00%</li></ul> |
* Samples:
  | sentence_1                                                                      | sentence_2                                                                                                                                            | label          |
  |:--------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------|
  | <code>query: le bruit des voisins , ronflement ect ..</code>                    | <code>query: à l’arrivée, on prend sur votre carte de crédit un montant supérieur au prix de la chambre, en caution « en cas de dégradation ».</code> | <code>1</code> |
  | <code>query: petit déjeuner top et accueil très agréable.</code>                | <code>query: bon fonctionnement du wifi très bon rapport qualité prix</code>                                                                          | <code>1</code> |
  | <code>query: l'emplacement et le restaurant à proximité en face du port.</code> | <code>query: le personnel est vraiment serviable souriant et agréable.</code>                                                                         | <code>1</code> |
* Loss: [<code>GISTEmbedLoss</code>](https://sbert.net/docs/package_reference/sentence_transformer/losses.html#gistembedloss) with these parameters:
  ```json
  {
      "guide": "SentenceTransformer('intfloat/multilingual-e5-large')",
      "temperature": 0.05,
      "margin_strategy": "absolute",
      "margin": 0.0,
      "contrast_anchors": true,
      "contrast_positives": true,
      "gather_across_devices": false
  }
  ```

### Training Hyperparameters
#### Non-Default Hyperparameters

- `eval_strategy`: steps
- `per_device_train_batch_size`: 128
- `num_train_epochs`: 1
- `bf16`: True
- `batch_sampler`: no_duplicates

#### All Hyperparameters
<details><summary>Click to expand</summary>

- `overwrite_output_dir`: False
- `do_predict`: False
- `eval_strategy`: steps
- `prediction_loss_only`: True
- `per_device_train_batch_size`: 128
- `per_device_eval_batch_size`: 8
- `per_gpu_train_batch_size`: None
- `per_gpu_eval_batch_size`: None
- `gradient_accumulation_steps`: 1
- `eval_accumulation_steps`: None
- `torch_empty_cache_steps`: None
- `learning_rate`: 5e-05
- `weight_decay`: 0.0
- `adam_beta1`: 0.9
- `adam_beta2`: 0.999
- `adam_epsilon`: 1e-08
- `max_grad_norm`: 1.0
- `num_train_epochs`: 1
- `max_steps`: -1
- `lr_scheduler_type`: linear
- `lr_scheduler_kwargs`: {}
- `warmup_ratio`: 0.0
- `warmup_steps`: 0
- `log_level`: passive
- `log_level_replica`: warning
- `log_on_each_node`: True
- `logging_nan_inf_filter`: True
- `save_safetensors`: True
- `save_on_each_node`: False
- `save_only_model`: False
- `restore_callback_states_from_checkpoint`: False
- `no_cuda`: False
- `use_cpu`: False
- `use_mps_device`: False
- `seed`: 42
- `data_seed`: None
- `jit_mode_eval`: False
- `use_ipex`: False
- `bf16`: True
- `fp16`: False
- `fp16_opt_level`: O1
- `half_precision_backend`: auto
- `bf16_full_eval`: False
- `fp16_full_eval`: False
- `tf32`: None
- `local_rank`: 0
- `ddp_backend`: None
- `tpu_num_cores`: None
- `tpu_metrics_debug`: False
- `debug`: []
- `dataloader_drop_last`: False
- `dataloader_num_workers`: 0
- `dataloader_prefetch_factor`: None
- `past_index`: -1
- `disable_tqdm`: False
- `remove_unused_columns`: True
- `label_names`: None
- `load_best_model_at_end`: False
- `ignore_data_skip`: False
- `fsdp`: []
- `fsdp_min_num_params`: 0
- `fsdp_config`: {'min_num_params': 0, 'xla': False, 'xla_fsdp_v2': False, 'xla_fsdp_grad_ckpt': False}
- `fsdp_transformer_layer_cls_to_wrap`: None
- `accelerator_config`: {'split_batches': False, 'dispatch_batches': None, 'even_batches': True, 'use_seedable_sampler': True, 'non_blocking': False, 'gradient_accumulation_kwargs': None}
- `deepspeed`: None
- `label_smoothing_factor`: 0.0
- `optim`: adamw_torch_fused
- `optim_args`: None
- `adafactor`: False
- `group_by_length`: False
- `length_column_name`: length
- `ddp_find_unused_parameters`: None
- `ddp_bucket_cap_mb`: None
- `ddp_broadcast_buffers`: False
- `dataloader_pin_memory`: True
- `dataloader_persistent_workers`: False
- `skip_memory_metrics`: True
- `use_legacy_prediction_loop`: False
- `push_to_hub`: False
- `resume_from_checkpoint`: None
- `hub_model_id`: None
- `hub_strategy`: every_save
- `hub_private_repo`: None
- `hub_always_push`: False
- `hub_revision`: None
- `gradient_checkpointing`: False
- `gradient_checkpointing_kwargs`: None
- `include_inputs_for_metrics`: False
- `include_for_metrics`: []
- `eval_do_concat_batches`: True
- `fp16_backend`: auto
- `push_to_hub_model_id`: None
- `push_to_hub_organization`: None
- `mp_parameters`: 
- `auto_find_batch_size`: False
- `full_determinism`: False
- `torchdynamo`: None
- `ray_scope`: last
- `ddp_timeout`: 1800
- `torch_compile`: False
- `torch_compile_backend`: None
- `torch_compile_mode`: None
- `include_tokens_per_second`: False
- `include_num_input_tokens_seen`: False
- `neftune_noise_alpha`: None
- `optim_target_modules`: None
- `batch_eval_metrics`: False
- `eval_on_start`: False
- `use_liger_kernel`: False
- `liger_kernel_config`: None
- `eval_use_gather_object`: False
- `average_tokens_across_devices`: False
- `prompts`: None
- `batch_sampler`: no_duplicates
- `multi_dataset_batch_sampler`: proportional
- `router_mapping`: {}
- `learning_rate_mapping`: {}

</details>

### Training Logs
| Epoch  | Step | Training Loss | sgts_spearman_cosine |
|:------:|:----:|:-------------:|:--------------------:|
| 0.1003 | 235  | 4.7033        | 0.4244               |
| 0.2005 | 470  | 4.4087        | 0.4129               |
| 0.3008 | 705  | 4.34          | 0.4155               |
| 0.4010 | 940  | 4.3018        | 0.4182               |
| 0.5013 | 1175 | 4.2716        | 0.4203               |
| 0.6015 | 1410 | 4.2734        | 0.4192               |
| 0.7018 | 1645 | 4.2562        | 0.4205               |
| 0.8020 | 1880 | 4.2483        | 0.4298               |
| 0.9023 | 2115 | 4.2374        | 0.4276               |


### Framework Versions
- Python: 3.11.7
- Sentence Transformers: 5.1.0
- Transformers: 4.55.0
- PyTorch: 2.8.0+cu128
- Accelerate: 1.10.0
- Datasets: 4.0.0
- Tokenizers: 0.21.4

## Citation

### BibTeX

#### Sentence Transformers
```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```

#### GISTEmbedLoss
```bibtex
@misc{solatorio2024gistembed,
    title={GISTEmbed: Guided In-sample Selection of Training Negatives for Text Embedding Fine-tuning},
    author={Aivin V. Solatorio},
    year={2024},
    eprint={2402.16829},
    archivePrefix={arXiv},
    primaryClass={cs.LG}
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->