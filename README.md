# Cuckoo Filter

This is the 2nd project in a series of 3 attempts at building more robust hash-based lookup structures. I made a cuckoo filter after making a bloom because I wanted to expand on bloom's use of fingerprints/multi-hashing by building a filter that was able to allow deletion. Cuckoo is unique to bloom by the way a value gets hashed to a singular buffer rather than scattered bits meaning the algorithm could be used for hashing which I eventually expanded on in my final project of this series [ICEBERG Hashing](https://github.com/Rydilly/Iceberg_Hash). 

## What is a cuckoo filter?

Cuckoo filters use fingerprints similar to my prior project on [Bloom_Filters](https://github.com/Rydilly/bloom_filter). The algorithm is named after the seemingly foolish behavior of the cuckoo bird: the first chick to hatch typically pushes the other eggs out of the nest to maximize resources for itself. Similarly, cuckoo hashing involves kicking out values on collision.

![Cuckoo bird pushing egg](cuckoo_bird.gif)

## How does it work?

1. An item gets a fingerprint and 2 independent hashes. Each hash points to a bucket.
2. Both buckets are iterated through until an empty slot is found.
3. If both buckets are full, a random slot is chosen and the value at that location gets sent to its *other* hash.
4. If that other bucket is also full, step 3 repeats; otherwise the value gets pushed out of its current location and into the address that does not have a conflict.

*Note: the key is stored as the fingerprint to avoid costly rehashing when "the egg is pushed to a new nest." To find the other hash, simply XOR the current index with the hash of the fingerprint. When it's time for lookup, you just search both buckets the value hashes to.*

## Does it actually work?

Yes. Running the self-tests in both files:

- Every inserted item is found afterwards (no false negatives at reasonable load).
- After inserting 3200 items and querying 10000, my false positive rate came out to about **0.004**.
- The theoretical worst case is about **0.031** for `b=4` and `f=8`, so real-world performance ends up much better because most buckets aren't fully packed.

Past around 0.8 capacity I run into issues with finding fewer items than I added. I'm assuming this is due to insertion failures, which seems high for an algorithm that loops 500 times every time it can't find an available slot.

## The math

- The odds that a given bucket cell has the same fingerprint I'm inserting is `1 / (2^f - 1)` (excluding 0, since `z XOR 0 == z`).
- The odds of *not* finding that fingerprint in either bucket is `(1 - 1/(2^f - 1))^(2b)`.
- So the odds of a false positive is `1 - (1 - 1/(2^f - 1))^(2b)` — about 0.031 for `b=4`, `f=8`.
- Approximation: `FPR ≈ 2b / 2^f`.

Solving for fingerprint length given a target false positive rate `z`:

```
f = ln(2b / z) / ln(2)
```

Solving for table size given a target capacity:

```
size = capacity / (bucket_size * 0.95)
```

The 0.95 is the load limit to avoid failed adds in most cases. Buckets with 1 slot start failing around 50% load; 8-slot buckets can push all the way to about 98%.

## How to use

There are two implementations in this repo:

- **`cuckoo.py`** — a straightforward version backed by a list of lists. Fixed 8-bit fingerprint, 4 slots per bucket.
- **`cuckoo_bytearray.py`** — a more optimized version backed by a raw `bytearray` for better cache locality. Fingerprint size is computed from your target false positive rate.

*cuckoo_bytearray is the 2nd iteration of cuckoo. If you wish to understand the logic of cuckoo algorithms I'd advise reading through cuckoo.*

```python
from cuckoo_bytearray import cuckoo_hash

# capacity = items you plan to store
# fpr = target false positive rate
c = cuckoo_hash(capacity=50000, fpr=0.01)

c.add(42)
c.add("hello")

c.contains(42)   # True
c.contains(999)  # False (probably — small chance of a false positive)

c.delete(42)
```

Both files run a small self-test when executed directly:

```
python cuckoo.py
python cuckoo_bytearray.py
```

Dependencies: `mmh3`.

## What did I learn?

After this project I became an advocate of DS&A curriculum including filters. They should suffice as a good introduction to hashing while also holding benefits in cache locality. Since a bucket slot is a single byte (or less), the total footprint of the buffer is tiny and lookup is incredibly fast compared to full-key hashing thanks to CPU cache line behavior.

I also hit an interesting edge case bug where my fingerprint hash was 0 resulting in an unchanged hash (any value xor by 0 is it's self) instead of a separate bucket the value could be stored in.
