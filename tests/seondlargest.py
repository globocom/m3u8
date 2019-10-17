t=int(input())
for i in range(t):
    n=list(map(int,input().split()))
    n=list(set(n))
    n.sort()
    print(n[-2])