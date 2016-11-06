def numFullRoutes(lst):
    first_stop = 6
    last_stop = 28
    start_index = 0
    total =0
    while first_stop in lst:
        i = lst.index(first_stop)
        if i+(last_stop-first_stop)<=len(lst):
            if lst[i:i+(last_stop-first_stop)] == range(first_stop,last_stop):
                total+=1
        start_index=i+1
        lst = lst[start_index:]
    return total

