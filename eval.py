from src.answer import answer

questions = [
    "What architecture does DMMGAN use to predict human motion?",
    "Why does the paper say predicting only one possible future motion is a limitation?",
    "What problem does multi-motion prediction solve for robotics applications?",
    "What classifiers does the paper use for multi-label emotion classification?",
    "Where do the basic emotion categories come from?",
    "Is this a binary classification or multi-label classification task?",
    "What is the core idiosyncrasy/problem the paper identifies with time-discretization in RL?",
    "Why do physical systems create a challenge for fixed time-step RL algorithms?",
    "Who are the authors of the time-discretization in RL paper?",
    "What does RVI stand for in the context of average-reward Q-learning?",
    "What type of MDPs does the average-reward Q-learning convergence analysis focus on?",
    "What is the average-reward criterion, as opposed to other reward criteria in RL?",
    "What kind of cybersecurity issues does the paper address for autonomous vehicles?",
    "Is this an academic research paper or a different kind of document?",
    "What degree program is the cybersecurity capstone project for?",
    "Which papers involve reinforcement learning?",
    "What is the main contribution of this paper?",
    "Summarize the abstract of the tweet emotion classification paper.",
    "What machine learning technique is used to classify emotions in tweets?",
    "Does any paper discuss generative adversarial networks?",
]

with open("eval_results.txt", "w", encoding="utf-8") as f:
    for i, q in enumerate(questions, 1):
        result = answer(q)
        sources_used = sorted(set(s["source"] for s in result["sources"]))
        
        f.write(f"Q{i}: {q}\n")
        f.write(f"Answer: {result['answer']}\n")
        f.write(f"Sources cited: {', '.join(sources_used)}\n")
        f.write(f"Grade (pass/partial/fail): \n")
        f.write("-" * 80 + "\n\n")
        print(f"Done Q{i}/20")

print("Eval complete. See eval_results.txt")