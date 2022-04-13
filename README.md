# DA-VSED
Implementation for the paper "Data Augmentation for Rare Symptoms in Vaccine Side-Effect Detection" (BioNLP 2022) in Pytorch

You can download full data [here](https://drive.google.com/drive/folders/1x33F1psLYYcRLDTwNhjMDg8vU5AGofC6?usp=sharing)

## Train 

```
python run_bart.py \
    --model_name_or_path facebook/bart-base \
    --max_source_length 256 \
    --max_target_length 128 \
    --per_device_train_batch_size 16 \
    --gradient_accumulation_steps 2 \
    --learning_rate 2e-5 \
    --num_train_epochs 5 \
    --output_dir {output_dir} \
    --text_column symptom_text \
    --summary_column symptoms \
    --train_file data/train.json \
    --validation_file data/dev.json \
    --do_train
```

## Test
```
python run_bart.py \
    --model_name_or_path {test_model_name_or_path} \
    --max_source_length 256 \
    --max_target_length 128 \
    --per_device_eval_batch_size 16 \
    --text_column symptom_text \
    --summary_column symptoms \
    --test_file data/test.json \
    --do_predict
```