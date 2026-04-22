## Performance

### Evaluation setup
- Dataset: 20 hand-written Q&A pairs on LangGraph docs
- Evaluators: correctness (LLM-as-judge), retrieval recall, latency
- Model: gpt-4o-mini

### Results

| Metric | k=2 (baseline) | k=4 | Change |
|---|---|---|---|
| Correctness | 0.885 | 0.930 | +0.045 |
| Retrieval recall | 0.816 | 0.831 | +0.015 |
| Latency (s) | 1.484 | 1.399 | -0.085 |

### Conclusion
Increasing k from 2 to 4 improved correctness by 4.5% with no 
latency penalty. More retrieved context helps the LLM answer 
more completely. k=4 is the better configuration for this dataset.

### Bottleneck
LLM generation (not retrieval) is the main latency cost.
Average 1.4s per question — most time spent on gpt-4o-mini call,
not on Chroma similarity search.