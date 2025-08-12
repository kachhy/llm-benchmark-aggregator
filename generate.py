# Generates leaderboard data
# Currently accepts epoch.ai benchmark data, will expand later

import pandas as pd
import sys

LOW_RUN_THRES  = 20 # The minimum number of test runs a test can be used for
LOW_TEST_THRES = 4 # The minimum number of test cases a model must have to be included

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 generate.py <input CSV>")
        return
        
    df = pd.read_csv(sys.argv[1])
    
    # Isolate tests into separate dataframes
    test_results = dict()
    for i, row in df.iterrows():
        if sum(df["task"].str.count(row["task"])) < 20: # Remove tests with low test numbers
            continue
        if test_results.get(row["task"]): # Somewhat bad assumption because of potentially flawed data: model has only one best score 
            test_results[row["task"]][row["model"]] = row["Best score (across scorers)"] 
        else:
            test_results[row["task"]] = {row["model"] : row["Best score (across scorers)"]}

    # Process test scores
    test_scores = dict()
    for test in test_results:
        worst_model = min(test_results[test], key=test_results[test].get)
        worst_score = test_results[test][worst_model]
        best_model  = max(test_results[test], key=test_results[test].get)
        best_score  = test_results[test][best_model]

        # Sanity check: If best score = worst score we skip this test since it is meaningless
        if best_score == worst_score:
            continue

        # Compute model for each score:
        test_scores[test] = dict()
        for model in test_results[test]:
            # Get relative score
            llm_score = test_results[test][model]
            rel_score = (llm_score - worst_score) / (best_score - worst_score)
            test_scores[test][model] = rel_score

    # Get average of all tests scores
    preproc_test_scores = dict()
    for test in test_scores:
        for model in test_scores[test]:
            if preproc_test_scores.get(model):
                preproc_test_scores[model][0] += test_scores[test][model]
                preproc_test_scores[model][1] += 1
            else:
                preproc_test_scores[model] = [test_scores[test][model], 1]
    
    average_test_scores = dict()
    for model in preproc_test_scores:
        if preproc_test_scores[model][1] < LOW_TEST_THRES: # Remove models with low test counts
            continue
        average_test_scores[model] = preproc_test_scores[model][0] / preproc_test_scores[model][1]
    
    result = sorted(average_test_scores, key=average_test_scores.get, reverse=True)

    for model in result:
        ats = round(average_test_scores[model] * 100, 1)
        print(f'{model:<38} {ats:<3}')

if __name__ == "__main__":
    main()