# Cuckoo Hash

This is the 2nd project in a series of 3 in attempts to make a more robust hashing function. 

## What is a cuckoo hash?
Cuckoo hashing use fingerprints for hashing simmilar to my prior project on [Bloom_Filters](https://github.com/Rydilly/bloom_filter). The algorithm is named after the seemingly foolish behavior of the Cuckoo bird. The First to hatch typically pushes the other eggs out of the nest to maximize resources for itself. Simmilarly Cuckoo hashing involves kicking out values on collision rather than linear probing.

[Cuckoo_Bird_Pushing_Egg](./cuckoo_bird.gif)

## How does it work?
1.An item gets a fingerprint of 2 independent hashes. Each buffer slot points to a bucket. 

2.both buckets are iterated through until an empty slot is found. 

3.If both buckets are exhausted a random slot is chosen and the value at that location sent to its other hash. 

4.If the other bucket is full 3 is repeated otherwise the value gets pushed out of its current location and to the address that does not have a conflict.  

*note the key is stored as the fingerprint to avoid costly rehashing when "the egg is pushed to a new nest" to find the other hash simply xor the current hash with the fingerprints hash. When its time for lookup you simply search both buckets the value is hashed to.
 
## Does it actually work?


## The math


## How to use?



## What did I learn?

After this project I became an advocate of DS&A curriculum including filters. They should suffice as a good introduction into hashing while also holding benefits in cache locality. Since a buffer slot was a single bit, the total space of the buffer was tiny and lookup was incredible compared to hashing due to CPU cache line restrictions.

