score=[1,22,443,432,343,2432,2,32,34,3]
max_score=0
for scores in score:
    if scores > max_score:
        max_score=scores
print(max_score)
