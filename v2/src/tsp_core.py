"""
tsp_core.py - fast (Numba) implementations used for the revised HBALS study.

All algorithms share:
  * the same distance matrix (TSPLIB EUC_2D, rounded to nearest integer),
  * the same 2-opt operator (first-improvement, restart after each move,
    capped number of improving moves) -- identical in semantics to the
    LocalSearch.two_opt_fast of the original src/hbals.py,
  * the same budget measure: a counter of "move evaluations" (see below).

Budget unit ("evaluation"):
  * one 2-opt / segment-reversal / swap delta  .......................  1
    (a swap delta is counted as 4)
  * one full tour-length computation  ................................  n
  * one ACO tour construction  .......................................  n*n/2
  * one OX crossover  ................................................  n
This makes budgets machine independent.
"""
import numpy as np
from numba import njit

BIG = 1 << 40


# ----------------------------------------------------------------------------
# basic utilities
# ----------------------------------------------------------------------------
def load_tsp(path):
    """Minimal TSPLIB reader for EUC_2D instances; returns (name, dist matrix)."""
    coords, name, section = [], None, False
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            if s.startswith("NAME"):
                name = s.split(":")[1].strip()
            elif s.startswith("EDGE_WEIGHT_TYPE"):
                if "EUC_2D" not in s:
                    raise ValueError("only EUC_2D supported: " + s)
            elif s.startswith("NODE_COORD_SECTION"):
                section = True
            elif s.startswith("EOF"):
                break
            elif section:
                p = s.split()
                coords.append((float(p[1]), float(p[2])))
    xy = np.array(coords)
    diff = xy[:, None, :] - xy[None, :, :]
    D = np.sqrt((diff ** 2).sum(-1))
    D = np.floor(D + 0.5)            # TSPLIB nint()
    return name, D.astype(np.float64)


@njit(cache=True)
def tour_len(t, D, cnt):
    n = t.shape[0]
    s = 0.0
    for i in range(n - 1):
        s += D[t[i], t[i + 1]]
    s += D[t[n - 1], t[0]]
    cnt[0] += n
    return s


@njit(cache=True)
def nn_tour(D, start, cnt):
    n = D.shape[0]
    visited = np.zeros(n, np.bool_)
    t = np.empty(n, np.int64)
    t[0] = start
    visited[start] = True
    cur = start
    for k in range(1, n):
        best = -1
        bd = 1e18
        for j in range(n):
            if (not visited[j]) and D[cur, j] < bd:
                bd = D[cur, j]
                best = j
        t[k] = best
        visited[best] = True
        cur = best
    cnt[0] += n * n // 2
    return t


@njit(cache=True)
def swap_delta(t, D, i, j):
    """Cost change of swapping the cities at positions i and j."""
    n = t.shape[0]
    if i > j:
        i, j = j, i
    if j == i + 1:
        a = t[(i - 1) % n]; b = t[i]; e = t[j]; f = t[(j + 1) % n]
        return D[a, e] + D[e, b] + D[b, f] - D[a, b] - D[b, e] - D[e, f]
    if i == 0 and j == n - 1:
        # positions n-1 and 0 are adjacent on the cycle
        a = t[n - 2]; b = t[n - 1]; e = t[0]; f = t[1]
        return D[a, e] + D[e, b] + D[b, f] - D[a, b] - D[b, e] - D[e, f]
    a = t[(i - 1) % n]; b = t[i]; c = t[i + 1]
    d = t[j - 1]; e = t[j]; f = t[(j + 1) % n]
    old = D[a, b] + D[b, c] + D[d, e] + D[e, f]
    new = D[a, e] + D[e, c] + D[d, b] + D[b, f]
    return new - old


@njit(cache=True)
def random_swap(t, D, cnt):
    """Apply one random swap in place, return the cost change."""
    n = t.shape[0]
    i = np.random.randint(0, n)
    j = np.random.randint(0, n)
    while j == i:
        j = np.random.randint(0, n)
    d = swap_delta(t, D, i, j)
    tmp = t[i]; t[i] = t[j]; t[j] = tmp
    cnt[0] += 4
    return d


# ----------------------------------------------------------------------------
# local search operators
# ----------------------------------------------------------------------------
@njit(cache=True)
def two_opt(t, D, max_moves, cnt):
    """First-improvement 2-opt, restarting the scan after every improving
    move (as in the original implementation).  Returns total cost change."""
    n = t.shape[0]
    moves = 0
    gain = 0.0
    ev = 0
    while moves < max_moves:
        found = False
        for i in range(1, n - 2):
            a = t[i - 1]
            b = t[i]
            Da = D[a]
            Db = D[b]
            dab = Da[b]
            for j in range(i + 2, n):
                c = t[j]
                if j + 1 < n:
                    d = t[j + 1]
                else:
                    d = t[0]
                delta = Da[c] + Db[d] - dab - D[c, d]
                if delta < -1e-9:
                    ev += j - i - 1
                    l = i
                    r = j
                    while l < r:
                        tmp = t[l]; t[l] = t[r]; t[r] = tmp
                        l += 1
                        r -= 1
                    gain += delta
                    moves += 1
                    found = True
                    break
            if found:
                break
            ev += n - i - 2
        if not found:
            break
    cnt[0] += ev
    return gain


@njit(cache=True)
def rev_light(t, D, tries, cnt):
    """The 'lightweight 3-opt-style' step of the original code: `tries`
    random segment reversals t[i..j-1] are evaluated independently, the best
    improving one (if any) is applied.  (It is a randomised 2-opt step, not a
    true 3-opt move - the paper now calls it 'random segment reversal'.)"""
    n = t.shape[0]
    best = 0.0
    bi = -1
    bj = -1
    for _ in range(tries):
        x = np.random.randint(1, n)
        y = np.random.randint(1, n)
        while y == x:
            y = np.random.randint(1, n)
        z = np.random.randint(1, n)
        while z == x or z == y:
            z = np.random.randint(1, n)
        # sort x<y<z
        if x > y:
            x, y = y, x
        if y > z:
            y, z = z, y
        if x > y:
            x, y = y, x
        i = x
        j = y
        a = t[i - 1]; b = t[i]; c = t[j - 1]; d = t[j]
        delta = D[a, c] + D[b, d] - D[a, b] - D[c, d]
        if delta < best - 1e-9:
            best = delta
            bi = i
            bj = j - 1
    cnt[0] += tries
    if bi >= 0:
        l = bi
        r = bj
        while l < r:
            tmp = t[l]; t[l] = t[r]; t[r] = tmp
            l += 1
            r -= 1
    return best


# ----------------------------------------------------------------------------
# HBALS (all variants through parameters)
# ----------------------------------------------------------------------------
# P index map
P_N, P_M, P_E, P_NEP, P_NSP, P_NGH, P_ALPHA, P_BETA, P_NNR, P_THR, \
    P_PEL, P_PSEL, P_P3, P_CAP, P_LSEL, P_LSSEL, P_REVT, P_ADAPT, P_SCOUT, \
    P_MAXIT = range(20)


def make_params(n=20, m=12, e=3, nep=8, nsp=4, ngh=3, alpha=0.9, beta=1.05,
                nn_ratio=0.5, thr=0, p_el=0.7, p_sel=0.3, p3=0.1, cap=10,
                ls_el=20, ls_sel=10, rev_tries=3, adapt=1, scouts=1,
                max_iter=0):
    """adapt: 0 = original integer-truncated rule (as published, which
    freezes at 1 swap), 1 = corrected floating-point rule capped at `cap`,
    2 = fixed neighbourhood `ngh`."""
    return np.array([n, m, e, nep, nsp, ngh, alpha, beta, nn_ratio, thr,
                     p_el, p_sel, p3, cap, ls_el, ls_sel, rev_tries, adapt,
                     scouts, max_iter], dtype=np.float64)


@njit(cache=True)
def search_site(base, base_cost, D, cnt, num, k, p_ls, ls_moves, p3, rev_tries):
    N = base.shape[0]
    best = base.copy()
    bc = base_cost
    cand = np.empty(N, np.int64)
    for _ in range(num):
        cand[:] = base
        c = base_cost
        for _s in range(k):
            c += random_swap(cand, D, cnt)
        if p_ls > 0.0 and np.random.random() < p_ls:
            c += two_opt(cand, D, ls_moves, cnt)
        if p3 > 0.0 and np.random.random() < p3:
            c += rev_light(cand, D, rev_tries, cnt)
        if c < bc:
            best[:] = cand
            bc = c
    return best, bc


@njit(cache=True)
def hbals(D, P, budget, seed, conv):
    """Returns (best_cost, best_tour, evaluations, iterations).
    conv (len 100) receives the best-so-far cost at each 1% of the budget."""
    np.random.seed(seed)
    N = D.shape[0]
    n_pop = int(P[0]); m = int(P[1]); e = int(P[2])
    nep = int(P[3]); nsp = int(P[4]); ngh0 = int(P[5])
    alpha = P[6]; beta = P[7]; nn_ratio = P[8]; thr = int(P[9])
    p_el = P[10]; p_sel = P[11]; p3 = P[12]; cap = P[13]
    ls_el = int(P[14]); ls_sel = int(P[15]); rev_t = int(P[16])
    mode = int(P[17]); scouts = int(P[18]); max_it = int(P[19])
    cnt = np.zeros(1, np.int64)

    pop = np.empty((n_pop, N), np.int64)
    costs = np.empty(n_pop, np.float64)
    num_nn = 0
    if nn_ratio > 0.0:
        num_nn = max(1, int(nn_ratio * n_pop))
    for r in range(n_pop):
        if r < num_nn and r < N:
            pop[r] = nn_tour(D, r, cnt)
        else:
            pop[r] = np.random.permutation(N)
        costs[r] = tour_len(pop[r], D, cnt)
    psize = n_pop

    bi = np.argmin(costs)
    best = pop[bi].copy()
    best_cost = costs[bi]
    noimp = 0
    cur_f = float(ngh0)
    cur_i = ngh0
    filled = 0
    it = 0
    cap_eff = min(cap, float(N // 2))

    while True:
        if budget > 0 and cnt[0] >= budget:
            break
        if max_it > 0 and it >= max_it:
            break
        # --- neighbourhood size -------------------------------------------
        if mode == 0:
            if noimp >= 3:
                cur_i = min(int(cur_i * beta), N // 2)
            else:
                cur_i = max(int(cur_i * alpha), 1)
            k = cur_i
        elif mode == 1:
            if noimp >= 3:
                cur_f = min(cur_f * beta, cap_eff)
            else:
                cur_f = max(cur_f * alpha, 1.0)
            k = max(1, int(cur_f))
        else:
            k = ngh0
        order = np.argsort(costs[:psize])
        new_size = n_pop if scouts == 1 else m
        npop2 = np.empty((new_size, N), np.int64)
        ncost = np.empty(new_size, np.float64)
        for r in range(e):
            idx = order[r]
            tb, tc = search_site(pop[idx], costs[idx], D, cnt, nep, k,
                                 p_el, ls_el, p3, rev_t)
            npop2[r] = tb
            ncost[r] = tc
        ks = max(1, k // 2)
        for r in range(e, m):
            idx = order[r]
            tb, tc = search_site(pop[idx], costs[idx], D, cnt, nsp, ks,
                                 p_sel, ls_sel, 0.0, 0)
            npop2[r] = tb
            ncost[r] = tc
        if scouts == 1:
            for r in range(m, n_pop):
                npop2[r] = np.random.permutation(N)
                ncost[r] = tour_len(npop2[r], D, cnt)
        pop = npop2
        costs = ncost
        psize = new_size
        ci = np.argmin(costs)
        if costs[ci] < best_cost:
            best_cost = costs[ci]
            best = pop[ci].copy()
            noimp = 0
        else:
            noimp += 1
        it += 1
        if budget > 0:
            slot = min(99, int(cnt[0] * 100 // budget))
            while filled <= slot:
                conv[filled] = best_cost
                filled += 1
        if thr > 0 and noimp >= thr:
            break
    while filled < 100:
        conv[filled] = best_cost
        filled += 1
    return best_cost, best, cnt[0], it


# ----------------------------------------------------------------------------
# baselines
# ----------------------------------------------------------------------------
@njit(cache=True)
def _fill(conv, filled, cnt, budget, best_cost):
    slot = min(99, int(cnt * 100 // budget))
    while filled <= slot:
        conv[filled] = best_cost
        filled += 1
    return filled


@njit(cache=True)
def ba_plain(D, budget, seed, conv, n_pop=20, m=12, e=3, nep=8, nsp=4, ngh=3):
    """Basic BA as in the original repository (random init, `ngh`
    independent one-swap neighbours per recruited bee, scouts) but with O(1)
    swap evaluation so that it can exploit the budget efficiently."""
    np.random.seed(seed)
    N = D.shape[0]
    cnt = np.zeros(1, np.int64)
    pop = np.empty((n_pop, N), np.int64)
    costs = np.empty(n_pop)
    for r in range(n_pop):
        pop[r] = np.random.permutation(N)
        costs[r] = tour_len(pop[r], D, cnt)
    bi = np.argmin(costs)
    best_cost = costs[bi]
    best = pop[bi].copy()
    filled = 0
    cand = np.empty(N, np.int64)
    while cnt[0] < budget:
        order = np.argsort(costs)
        npop2 = np.empty((n_pop, N), np.int64)
        ncost = np.empty(n_pop)
        for r in range(m):
            idx = order[r]
            num = nep if r < e else nsp
            sb = pop[idx].copy()
            sc = costs[idx]
            for _ in range(num):
                cbest_c = costs[idx]
                cbest_i = -1
                cbest_j = -1
                for _g in range(ngh):
                    i = np.random.randint(0, N)
                    j = np.random.randint(0, N)
                    while j == i:
                        j = np.random.randint(0, N)
                    d = swap_delta(pop[idx], D, i, j)
                    cnt[0] += 4
                    if costs[idx] + d < cbest_c:
                        cbest_c = costs[idx] + d
                        cbest_i = i
                        cbest_j = j
                if cbest_c < sc:
                    sb[:] = pop[idx]
                    tmp = sb[cbest_i]; sb[cbest_i] = sb[cbest_j]; sb[cbest_j] = tmp
                    sc = cbest_c
            npop2[r] = sb
            ncost[r] = sc
        for r in range(m, n_pop):
            npop2[r] = np.random.permutation(N)
            ncost[r] = tour_len(npop2[r], D, cnt)
        pop = npop2
        costs = ncost
        ci = np.argmin(costs)
        if costs[ci] < best_cost:
            best_cost = costs[ci]
            best = pop[ci].copy()
        filled = _fill(conv, filled, cnt[0], budget, best_cost)
    while filled < 100:
        conv[filled] = best_cost
        filled += 1
    return best_cost, best, cnt[0], 0


@njit(cache=True)
def multistart_2opt(D, budget, seed, conv):
    np.random.seed(seed)
    N = D.shape[0]
    cnt = np.zeros(1, np.int64)
    best_cost = 1e18
    best = np.arange(N)
    filled = 0
    it = 0
    while cnt[0] < budget:
        t = np.random.permutation(N)
        c = tour_len(t, D, cnt)
        c += two_opt(t, D, BIG, cnt)
        if c < best_cost:
            best_cost = c
            best = t.copy()
        it += 1
        filled = _fill(conv, filled, cnt[0], budget, best_cost)
    while filled < 100:
        conv[filled] = best_cost
        filled += 1
    return best_cost, best, cnt[0], it


@njit(cache=True)
def double_bridge(t, out):
    n = t.shape[0]
    a = np.random.randint(1, n)
    b = np.random.randint(1, n)
    while b == a:
        b = np.random.randint(1, n)
    c = np.random.randint(1, n)
    while c == a or c == b:
        c = np.random.randint(1, n)
    if a > b:
        a, b = b, a
    if b > c:
        b, c = c, b
    if a > b:
        a, b = b, a
    k = 0
    for x in range(0, a):
        out[k] = t[x]; k += 1
    for x in range(b, c):
        out[k] = t[x]; k += 1
    for x in range(a, b):
        out[k] = t[x]; k += 1
    for x in range(c, n):
        out[k] = t[x]; k += 1


@njit(cache=True)
def ils_2opt(D, budget, seed, conv):
    """Iterated local search: NN start, double-bridge kick, full 2-opt
    descent (same operator as HBALS), accept if not worse."""
    np.random.seed(seed)
    N = D.shape[0]
    cnt = np.zeros(1, np.int64)
    cur = nn_tour(D, np.random.randint(0, N), cnt)
    c = tour_len(cur, D, cnt)
    c += two_opt(cur, D, BIG, cnt)
    best = cur.copy()
    best_cost = c
    cand = np.empty(N, np.int64)
    filled = 0
    it = 0
    while cnt[0] < budget:
        double_bridge(cur, cand)
        cc = tour_len(cand, D, cnt)
        cc += two_opt(cand, D, BIG, cnt)
        if cc <= c:
            cur[:] = cand
            c = cc
            if c < best_cost:
                best_cost = c
                best = cur.copy()
        it += 1
        filled = _fill(conv, filled, cnt[0], budget, best_cost)
    while filled < 100:
        conv[filled] = best_cost
        filled += 1
    return best_cost, best, cnt[0], it


@njit(cache=True)
def _ox(p1, p2, child, used):
    n = p1.shape[0]
    s = np.random.randint(0, n)
    e = np.random.randint(0, n)
    while e == s:
        e = np.random.randint(0, n)
    if s > e:
        s, e = e, s
    used[:] = False
    child[:] = -1
    for x in range(s, e + 1):
        child[x] = p1[x]
        used[p1[x]] = True
    pos = (e + 1) % n
    q = (e + 1) % n
    filled = e - s + 1
    while filled < n:
        g = p2[q]
        if not used[g]:
            child[pos] = g
            used[g] = True
            pos = (pos + 1) % n
            filled += 1
        q = (q + 1) % n


@njit(cache=True)
def ga_ls(D, budget, seed, conv, pop_size=20, pc=0.8, pm=0.1, tsize=3,
          elit=2, ls_moves=20):
    """Memetic GA: the repository GA (OX, swap mutation, tournament,
    elitism) with the same 2-opt applied to every offspring."""
    np.random.seed(seed)
    N = D.shape[0]
    cnt = np.zeros(1, np.int64)
    pop = np.empty((pop_size, N), np.int64)
    costs = np.empty(pop_size)
    for r in range(pop_size):
        pop[r] = np.random.permutation(N)
        costs[r] = tour_len(pop[r], D, cnt)
    bi = np.argmin(costs)
    best_cost = costs[bi]
    best = pop[bi].copy()
    used = np.zeros(N, np.bool_)
    filled = 0
    while cnt[0] < budget:
        order = np.argsort(costs)
        npop2 = np.empty((pop_size, N), np.int64)
        ncost = np.empty(pop_size)
        for r in range(elit):
            npop2[r] = pop[order[r]]
            ncost[r] = costs[order[r]]
        for r in range(elit, pop_size):
            # tournament parents
            pa = -1
            pb = -1
            for tix in range(2):
                bsel = np.random.randint(0, pop_size)
                for _ in range(tsize - 1):
                    q = np.random.randint(0, pop_size)
                    if costs[q] < costs[bsel]:
                        bsel = q
                if tix == 0:
                    pa = bsel
                else:
                    pb = bsel
            child = np.empty(N, np.int64)
            if np.random.random() < pc:
                _ox(pop[pa], pop[pb], child, used)
                cnt[0] += N
            else:
                child[:] = pop[pa]
            if np.random.random() < pm:
                i = np.random.randint(0, N)
                j = np.random.randint(0, N)
                while j == i:
                    j = np.random.randint(0, N)
                tmp = child[i]; child[i] = child[j]; child[j] = tmp
            c = tour_len(child, D, cnt)
            c += two_opt(child, D, ls_moves, cnt)
            npop2[r] = child
            ncost[r] = c
        pop = npop2
        costs = ncost
        ci = np.argmin(costs)
        if costs[ci] < best_cost:
            best_cost = costs[ci]
            best = pop[ci].copy()
        filled = _fill(conv, filled, cnt[0], budget, best_cost)
    while filled < 100:
        conv[filled] = best_cost
        filled += 1
    return best_cost, best, cnt[0], 0


@njit(cache=True)
def aco_ls(D, budget, seed, conv, n_ants=20, alpha=1.0, beta=2.0, rho=0.5,
           Q=100.0, tau0=0.1, ls_moves=20):  # alpha fixed to 1 (repository value)
    """Ant System as in the repository, with the same 2-opt applied to every
    ant's tour before the pheromone update."""
    np.random.seed(seed)
    N = D.shape[0]
    cnt = np.zeros(1, np.int64)
    eta = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            if D[i, j] > 0:
                eta[i, j] = (1.0 / D[i, j]) ** beta
    tau = np.full((N, N), tau0)
    best_cost = 1e18
    best = np.arange(N)
    filled = 0
    unv = np.empty(N, np.int64)
    w = np.empty(N)
    tours = np.empty((n_ants, N), np.int64)
    tcost = np.empty(n_ants)
    while cnt[0] < budget:
        for a in range(n_ants):
            start = np.random.randint(0, N)
            t = tours[a]
            t[0] = start
            nu = 0
            for c in range(N):
                if c != start:
                    unv[nu] = c
                    nu += 1
            cur = start
            for k in range(1, N):
                tot = 0.0
                for q in range(nu):
                    j = unv[q]
                    w[q] = tau[cur, j] * eta[cur, j]   # alpha = 1
                    tot += w[q]
                if tot > 0:
                    r = np.random.random() * tot
                    acc = 0.0
                    pick = nu - 1
                    for q in range(nu):
                        acc += w[q]
                        if acc >= r:
                            pick = q
                            break
                else:
                    pick = np.random.randint(0, nu)
                nxt = unv[pick]
                unv[pick] = unv[nu - 1]
                nu -= 1
                t[k] = nxt
                cur = nxt
            cnt[0] += N * N // 2
            c = tour_len(t, D, cnt)
            c += two_opt(t, D, ls_moves, cnt)
            tcost[a] = c
            if c < best_cost:
                best_cost = c
                best = t.copy()
        tau *= (1.0 - rho)
        cnt[0] += N * N // 8
        for a in range(n_ants):
            dep = Q / tcost[a]
            t = tours[a]
            for i in range(N):
                u = t[i]
                v = t[(i + 1) % N]
                tau[u, v] += dep
                tau[v, u] += dep
        filled = _fill(conv, filled, cnt[0], budget, best_cost)
    while filled < 100:
        conv[filled] = best_cost
        filled += 1
    return best_cost, best, cnt[0], 0


def check_tour(t, D, cost):
    n = D.shape[0]
    assert len(t) == n and len(set(t.tolist())) == n, "invalid permutation"
    c = sum(D[t[i], t[(i + 1) % n]] for i in range(n))
    assert abs(c - cost) < 1e-6, f"cost mismatch {c} vs {cost}"
    return c
