# MomoCode 算法知识图谱与训练手册

> 版本：0.1\
> 定位：ICPC / CCPC 训练知识地图，按铜牌、银牌、金牌三个训练层级组织。\
> 语言：C++17（模板以竞赛常用写法为主）。\
> 题库：Codeforces（下文简称 CF）、牛客（Nowcoder）、洛谷（Luogu）。\
> 重要说明：铜 / 银 / 金是 MomoCode 的训练分层，不是 ICPC
> 官方知识点认证标准；同一知识点可能跨层出现，难度取决于题目约束、建模与组合方式。

------------------------------------------------------------------------

## 目录

-   [0. 使用说明与考频口径](#0-使用说明与考频口径)
-   [1. 铜牌基础层 Bronze](#1-铜牌基础层-bronze)
    -   [1.1 基础数据结构](#11-基础数据结构)
    -   [1.2 基础图论](#12-基础图论)
    -   [1.3 基础动态规划与搜索](#13-基础动态规划与搜索)
    -   [1.4 基础数学与字符串](#14-基础数学与字符串)
-   [2. 银牌进阶层 Silver](#2-银牌进阶层-silver)
    -   [2.1 进阶数据结构](#21-进阶数据结构)
    -   [2.2 进阶图论](#22-进阶图论)
    -   [2.3 进阶 DP 与算法设计](#23-进阶-dp-与算法设计)
    -   [2.4 进阶数学与字符串](#24-进阶数学与字符串)
-   [3. 金牌拓展层 Gold](#3-金牌拓展层-gold)
    -   [3.1 高级数据结构](#31-高级数据结构)
    -   [3.2 高级图论](#32-高级图论)
    -   [3.3 高级 DP、数学与计算几何](#33-高级-dp数学与计算几何)
-   [4. 题目链接索引](#4-题目链接索引)
-   [5. 与 jiangly 模板 PDF
    的对应关系](#5-与-jiangly-模板-pdf-的对应关系)
-   [6. MomoCode 数据化建议](#6-momocode-数据化建议)

------------------------------------------------------------------------

## 0. 使用说明与考频口径

### 0.1 三层的含义

  ----------------------------------------------------------------------------------------------
  层级                    训练目标                达标表现
  ----------------------- ----------------------- ----------------------------------------------
  铜牌 Bronze             Know → Implement        能识别常见模型，独立写出基础模板，处理标准题

  银牌 Silver             Implement → Apply       能把模板嵌入复杂建模，处理多知识点组合与变形

  金牌 Gold               Apply → Optimize        能处理高级结构、复杂证明、离线技巧与性能优化
  ----------------------------------------------------------------------------------------------

层级不是知识点的永久标签。例如 Dijkstra
属于基础必备，但在高级图论题中仍可能作为子过程；线段树属于银牌核心，但基础单点查询题可作为铜牌入门。

### 0.2 ICPC / CCPC 考频统计

本版不伪造"某算法历年出现 N
次"的精确数字。要得到可复核的次数，必须先固定：

1.  **赛事范围**：ICPC World Finals、区域赛、邀请赛是否都计入；CCPC
    总决赛、分站赛、女生赛是否都计入。
2.  **年份范围**：建议先统计 2015---2025，之后每年增量更新。
3.  **题目去重规则**：同一题在不同赛事复用，按"出现次数"计还是按"不同题目数"计。
4.  **知识点标注规则**：一道题可能同时涉及
    DP、图论、数据结构；多标签计数会导致总和大于题目总数。
5.  **证据来源**：题面、官方题解、官方代码或可靠训练营题解。仅凭题目标题不能判定算法标签。

ICPC Problem Archive 的公开统计页面显示：其覆盖 2,475 场已举办赛事中的
1,341 场，记录 9,523
道问题；档案仍在持续补录。因此，当前公开数据不能直接代表完整历史赛事全集。

-   [ICPC Problem Archive](https://icpc.io/archive/)
-   [ICPC
    Archive：按赛事查看题目收录情况](https://icpc-contest-archive.github.io/contests/problems/index.html)
-   [ICPC
    Archive：题目总表](https://icpc-contest-archive.github.io/contests/problem/index.html)

#### 本版考频字段的解释

  ------------------------------------------------------------------------------
  标记                                含义
  ----------------------------------- ------------------------------------------
  高频（定性）                        多数 ICPC / CCPC
                                      训练体系中的常见基础模型；不是精确计数

  中频（定性）                        区域赛中较常见，通常需要一定建模或组合

  低频 / 专题                         专题型或高阶技巧，出现依赖赛区与年份

  待统计                              需要基于完整题目集逐题标注后才能给出次数
  ------------------------------------------------------------------------------

**MomoCode 正式版本应保存两个字段：**
`contest_occurrences`（出现赛事次数）与
`problem_occurrences`（题目出现次数），不要混为一谈。每条统计必须附年份范围、赛事范围、标签依据与数据更新时间。

------------------------------------------------------------------------

# 1. 铜牌基础层 Bronze

## 1.1 基础数据结构

### 1.1.1 排序、二分查找与二分答案

-   **用途 / 能解决的问题**
    -   排序后快速建立大小关系，配合双指针、贪心、离散化。
    -   二分查找有序数组中的边界。
    -   二分答案：答案具有单调性时，判断某个答案是否可行。
-   **最简单实现**
    -   排序：`sort(a.begin(), a.end())`。
    -   查找：维护 `[l,r)`，每次检查中点。
    -   二分答案：写 `check(mid)`，保证可行性随答案单调变化。
-   **C++ 模板**

``` cpp
// first position with a[i] >= x
int lowerBound(const vector<int>& a, int x) {
    int l = 0, r = (int)a.size();
    while (l < r) {
        int m = l + (r - l) / 2;
        if (a[m] >= x) r = m;
        else l = m + 1;
    }
    return l;
}

// minimum feasible answer in [lo, hi]
long long firstTrue(long long lo, long long hi) {
    while (lo < hi) {
        long long mid = lo + (hi - lo) / 2;
        if (check(mid)) hi = mid;
        else lo = mid + 1;
    }
    return lo;
}
```

-   **题目**
    -   经典： [CF 706B - Interesting
        drink](https://codeforces.com/problemset/problem/706/B)；[洛谷
        P2249 - 查找](https://www.luogu.com.cn/problem/P2249)
    -   进阶： [CF 670D1 - Magic
        Powder](https://codeforces.com/problemset/problem/670/D1)；[洛谷
        P1163 - 银行贷款](https://www.luogu.com.cn/problem/P1163)
    -   拓展： [CF 1486C1 - Guessing the
        Greatest](https://codeforces.com/problemset/problem/1486/C1)（交互式边界推理）
    -   牛客补充：[牛客题库搜索：二分](https://www.nowcoder.com/exam/oj)
-   **ICPC / CCPC 考频**：高频（定性）；精确次数待统计。
-   **关联**： [排序](#111-排序二分查找与二分答案) ·
    [双指针](#111-排序二分查找与二分答案) · [贪心](#132-贪心) ·
    [离散化](#211-离散化与差分)

### 1.1.2 前缀和与差分

-   **用途**：静态数组区间求和；频繁区间加、最后统一还原；二维矩阵子矩形求和。
-   **最简单实现**：前缀和 `pre[i+1]=pre[i]+a[i]`，区间 `[l,r)` 为
    `pre[r]-pre[l]`；差分只修改端点，最后做前缀累加。
-   **C++ 模板**

``` cpp
vector<long long> buildPrefix(const vector<int>& a) {
    int n = a.size();
    vector<long long> pre(n + 1);
    for (int i = 0; i < n; ++i) pre[i + 1] = pre[i] + a[i];
    return pre;
}
// sum [l, r)
long long rangeSum(const vector<long long>& pre, int l, int r) {
    return pre[r] - pre[l];
}
// add v to inclusive interval [l, r]
void rangeAdd(vector<long long>& diff, int l, int r, long long v) {
    diff[l] += v;
    diff[r + 1] -= v;
}
```

-   **题目**
    -   经典：[洛谷 P8218 -
        求区间和](https://www.luogu.com.cn/problem/P8218)；[CF 433B -
        Kuriyama Mirai's
        Stones](https://codeforces.com/problemset/problem/433/B)
    -   进阶：[洛谷 P3397 -
        地毯](https://www.luogu.com.cn/problem/P3397)；[CF 295A - Greg
        and Array](https://codeforces.com/problemset/problem/295/A)
    -   拓展：[CF 1555C - Coin
        Rows](https://codeforces.com/problemset/problem/1555/C)
    -   牛客补充：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：高频（定性）；精确次数待统计。
-   **关联**：[树状数组](#112-树状数组-fenwick) ·
    [扫描线](#331-计算几何与扫描线)

### 1.1.3 树状数组 Fenwick

-   **用途**：单点加、前缀和、区间和；逆序对；动态频率统计；支持按前缀和查找第
    k 个元素（要求频率非负）。
-   **最简单实现**：下标 `i` 的负责区间长度为 `lowbit(i)=i&-i`；更新时
    `i+=lowbit(i)`，查询时 `i-=lowbit(i)`。
-   **C++ 模板**

``` cpp
struct Fenwick {
    int n;
    vector<long long> bit;
    Fenwick(int n) : n(n), bit(n + 1) {}
    void add(int x, long long v) {
        for (; x <= n; x += x & -x) bit[x] += v;
    }
    long long sumPrefix(int x) const {
        long long s = 0;
        for (; x > 0; x -= x & -x) s += bit[x];
        return s;
    }
    long long rangeSum(int l, int r) const {
        return sumPrefix(r) - sumPrefix(l - 1);
    }
};
```

-   **题目**
    -   经典：[洛谷 P3374 - 树状数组
        1](https://www.luogu.com.cn/problem/P3374)
    -   进阶：[洛谷 P1908 -
        逆序对](https://www.luogu.com.cn/problem/P1908)；[CF 61E - Enemy
        is weak](https://codeforces.com/problemset/problem/61/E)
    -   拓展：[CF 799C -
        Fountains](https://codeforces.com/problemset/problem/799/C)（排序 +
        数据结构综合）
    -   牛客补充：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：中高频（定性）；精确次数待统计。
-   **关联**：[离散化](#211-离散化与差分) ·
    [线段树](#212-线段树与懒标记) · [逆序对](#112-树状数组-fenwick)

### 1.1.4 并查集 DSU

-   **用途**：维护动态连通块；判断两点是否连通；合并集合；Kruskal
    最小生成树。
-   **最简单实现**：父节点数组；路径压缩 + 按大小合并，均摊近似常数。
-   **C++ 模板**

``` cpp
struct DSU {
    vector<int> p, sz;
    DSU(int n) : p(n), sz(n, 1) { iota(p.begin(), p.end(), 0); }
    int find(int x) { return p[x] == x ? x : p[x] = find(p[x]); }
    bool unite(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return false;
        if (sz[a] < sz[b]) swap(a, b);
        p[b] = a; sz[a] += sz[b];
        return true;
    }
};
```

-   **题目**
    -   经典：[洛谷 P3367 -
        并查集](https://www.luogu.com.cn/problem/P3367)；[CF Disjoint
        Set Union 标签题](https://codeforces.com/problemset?tags=dsu)
    -   进阶：[洛谷 P1196 -
        银河英雄传说](https://www.luogu.com.cn/problem/P1196)；[CF
        1559D1 - Mocha and
        Diana](https://codeforces.com/problemset/problem/1559/D1)
    -   拓展：[CF 1706E - Qpwoeirst's connected
        subsets](https://codeforces.com/problemset/problem/1706/E)
    -   牛客补充：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：高频（定性）；精确次数待统计。
-   **关联**：[最小生成树](#121-图遍历与最小生成树) ·
    [可撤销并查集](#213-可撤销并查集) · [离线分治](#213-可撤销并查集)

## 1.2 基础图论

### 1.2.1 图遍历与最小生成树

-   **用途**：DFS/BFS 求连通性、层数、遍历序；Kruskal
    求连通所有点的最小总边权。
-   **最简单实现**：邻接表存图；BFS 用队列；Kruskal 按边权排序并用 DSU
    选边。
-   **C++ 模板**

``` cpp
vector<vector<int>> g(n);
vector<int> dist(n, -1);
queue<int> q;
dist[s] = 0; q.push(s);
while (!q.empty()) {
    int u = q.front(); q.pop();
    for (int v : g[u]) if (dist[v] == -1) {
        dist[v] = dist[u] + 1;
        q.push(v);
    }
}
// Kruskal
struct Edge { int u, v; long long w; };
sort(edges.begin(), edges.end(), [](auto a, auto b){ return a.w < b.w; });
DSU dsu(n);
long long mst = 0;
for (auto e : edges) if (dsu.unite(e.u, e.v)) mst += e.w;
```

-   **题目**
    -   经典：[洛谷 P3366 -
        最小生成树](https://www.luogu.com.cn/problem/P3366)；[CF 580C -
        Kefa and Park](https://codeforces.com/problemset/problem/580/C)
    -   进阶：[洛谷 P1111 -
        修复公路](https://www.luogu.com.cn/problem/P1111)；[CF 1249B1 -
        Books
        Exchange](https://codeforces.com/problemset/problem/1249/B1)
    -   拓展：[CF 160D - Edges in
        MST](https://codeforces.com/problemset/problem/160/D)
    -   牛客补充：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：高频（定性）；精确次数待统计。
-   **关联**：[并查集](#114-并查集-dsu) · [Dijkstra](#122-最短路) ·
    [SCC](#221-强连通分量-scc)

### 1.2.2 最短路

-   **用途**：求单源最短路径；Dijkstra 适用于非负边权，Bellman-Ford
    可处理负边并检测负环，Floyd 适合小规模全源最短路。
-   **最简单实现**：Dijkstra
    用小根堆，每次取当前距离最小的未确定状态并松弛邻边。
-   **C++ 模板（Dijkstra）**

``` cpp
using PLI = pair<long long, int>;
vector<vector<pair<int,int>>> g(n);
const long long INF = (1LL << 60);
vector<long long> dist(n, INF);
priority_queue<PLI, vector<PLI>, greater<PLI>> pq;
dist[s] = 0; pq.push({0, s});
while (!pq.empty()) {
    auto [d, u] = pq.top(); pq.pop();
    if (d != dist[u]) continue;
    for (auto [v, w] : g[u]) if (dist[v] > d + w) {
        dist[v] = d + w;
        pq.push({dist[v], v});
    }
}
```

-   **题目**
    -   经典：[洛谷 P4779 -
        单源最短路径（标准版）](https://www.luogu.com.cn/problem/P4779)；[CF
        20C - Dijkstra?](https://codeforces.com/problemset/problem/20/C)
    -   进阶：[洛谷 P1629 -
        邮递员送信](https://www.luogu.com.cn/problem/P1629)；[CF
        148D?](https://codeforces.com/problemset?tags=shortest%20paths)
    -   拓展：[CF 1915G -
        Bicycles](https://codeforces.com/problemset/problem/1915/G)
    -   牛客补充：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：高频（定性）；精确次数待统计。
-   **关联**：[堆](#111-排序二分查找与二分答案) · [Floyd](#122-最短路) ·
    [最小费用流](#222-网络流)

## 1.3 基础动态规划与搜索

### 1.3.1 线性 DP、背包与 LIS

-   **用途**：把问题拆成阶段状态；背包处理容量限制下的最优选择；LIS
    求最长严格上升子序列。
-   **最简单实现**：定义状态 `dp[i]`，写清转移、初值、遍历顺序；0/1
    背包容量倒序。
-   **C++ 模板**

``` cpp
// 0/1 knapsack
vector<long long> dp(W + 1);
for (int i = 0; i < n; ++i)
    for (int j = W; j >= w[i]; --j)
        dp[j] = max(dp[j], dp[j - w[i]] + val[i]);

// LIS, O(n log n)
vector<int> tail;
for (int x : a) {
    auto it = lower_bound(tail.begin(), tail.end(), x);
    if (it == tail.end()) tail.push_back(x);
    else *it = x;
}
```

-   **题目**
    -   经典：[洛谷 P1048 -
        采药](https://www.luogu.com.cn/problem/P1048)；[洛谷 P1439 -
        最长公共子序列](https://www.luogu.com.cn/problem/P1439)
    -   进阶：[CF 455A -
        Boredom](https://codeforces.com/problemset/problem/455/A)；[CF
        474D - Flowers](https://codeforces.com/problemset/problem/474/D)
    -   拓展：[CF 607B -
        Zuma](https://codeforces.com/problemset/problem/607/B)
    -   牛客补充：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：高频（定性）；精确次数待统计。
-   **关联**：[树形 DP](#232-树形dp与状压dp) · [数位
    DP](#232-树形dp与状压dp) · [LIS 优化](#232-树形dp与状压dp)

### 1.3.2 贪心

-   **用途**：在满足交换性质或其他正确性证明的前提下，每一步选择局部最优决策。
-   **最简单实现**：先排序，再按规则选择；重点不是代码，而是证明局部选择不会损害全局最优。
-   **C++ 模板**

``` cpp
sort(items.begin(), items.end(), [](const auto& a, const auto& b) {
    return a.key < b.key;
});
long long ans = 0;
for (const auto& x : items) {
    if (canChoose(x)) {
        choose(x);
        ans += x.cost;
    }
}
```

-   **题目**
    -   经典：[CF 1353B - Two Arrays And
        Swaps](https://codeforces.com/problemset/problem/1353/B)；[洛谷
        P1090 - 合并果子](https://www.luogu.com.cn/problem/P1090)
    -   进阶：[CF
        贪心标签题库](https://codeforces.com/problemset?tags=greedy)；[洛谷
        P1803 - 凌乱的yyy](https://www.luogu.com.cn/problem/P1803)
    -   拓展：[CF 1363E - Tree
        Shuffling](https://codeforces.com/problemset/problem/1363/E)
    -   牛客补充：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：高频（定性）；精确次数待统计。
-   **关联**：[排序](#111-排序二分查找与二分答案) ·
    [区间调度](#132-贪心) · [DP](#131-线性-dp背包与-lis)

### 1.3.3 DFS / BFS / 回溯与基础搜索

-   **用途**：状态空间遍历、连通块、网格最短步数、枚举组合与剪枝。
-   **最简单实现**：明确状态、合法转移、访问标记；回溯在递归返回时撤销选择。
-   **C++ 模板**

``` cpp
void dfs(int u) {
    vis[u] = true;
    for (int v : g[u]) if (!vis[v]) dfs(v);
}
```

-   **题目**
    -   经典：[洛谷 P1451 -
        求细胞数量](https://www.luogu.com.cn/problem/P1451)；[CF 580A -
        Kefa and First
        Steps](https://codeforces.com/problemset/problem/580/A)
    -   进阶：[洛谷 P1141 -
        01迷宫](https://www.luogu.com.cn/problem/P1141)；[CF 110A -
        Nearly Lucky
        Number](https://codeforces.com/problemset/problem/110/A)
    -   拓展：[CF 1513C - Add
        One](https://codeforces.com/problemset/problem/1513/C)（状态建模）
    -   牛客补充：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：高频（定性）；精确次数待统计。
-   **关联**：[树形 DP](#232-树形dp与状压dp) ·
    [SCC](#221-强连通分量-scc) · [记忆化搜索](#131-线性-dp背包与-lis)

## 1.4 基础数学与字符串

### 1.4.1 GCD、快速幂、素数筛与组合数基础

-   **用途**：最大公约数、模幂、素数判定/预处理、组合计数。
-   **最简单实现**：辗转相除法；快速幂按二进制拆指数；埃氏筛或线性筛预处理素数。
-   **C++ 模板**

``` cpp
long long qpow(long long a, long long b, long long mod) {
    long long r = 1 % mod;
    for (; b; b >>= 1, a = a * a % mod)
        if (b & 1) r = r * a % mod;
    return r;
}
int gcdInt(int a, int b) { return b ? gcdInt(b, a % b) : a; }
vector<int> primes, lp;
void linearSieve(int n) {
    lp.assign(n + 1, 0);
    for (int i = 2; i <= n; ++i) {
        if (!lp[i]) lp[i] = i, primes.push_back(i);
        for (int p : primes) {
            if (p > lp[i] || 1LL * i * p > n) break;
            lp[i * p] = p;
        }
    }
}
```

-   **题目**
    -   经典：[洛谷 P1226 -
        快速幂](https://www.luogu.com.cn/problem/P1226)；[洛谷 P3383 -
        线性筛素数](https://www.luogu.com.cn/problem/P3383)
    -   进阶：[CF 776B - Sherlock and his
        girlfriend](https://codeforces.com/problemset/problem/776/B)；[洛谷
        P1313 - 计算系数](https://www.luogu.com.cn/problem/P1313)
    -   拓展：[CF 1499E - Chaotic
        Merge](https://codeforces.com/problemset/problem/1499/E)
    -   牛客补充：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：高频（定性）；精确次数待统计。
-   **关联**：[欧拉函数](#241-进阶数论) · [组合数学](#241-进阶数论) ·
    [Miller-Rabin](#241-进阶数论)

### 1.4.2 KMP、Trie 与字符串哈希

-   **用途**：KMP 在线性时间匹配模式串；Trie
    维护字符串集合前缀；哈希快速比较子串（存在碰撞风险）。
-   **最简单实现**：KMP 预处理前缀函数；Trie
    按字符逐层建点；哈希用前缀哈希减去区间前缀。
-   **C++ 模板（KMP 前缀函数）**

``` cpp
vector<int> prefixFunction(const string& s) {
    int n = s.size();
    vector<int> pi(n);
    for (int i = 1; i < n; ++i) {
        int j = pi[i - 1];
        while (j && s[i] != s[j]) j = pi[j - 1];
        if (s[i] == s[j]) ++j;
        pi[i] = j;
    }
    return pi;
}
```

-   **题目**
    -   经典：[洛谷 P3375 -
        KMP字符串匹配](https://www.luogu.com.cn/problem/P3375)；[CF
        471D - MUH and Cube
        Walls](https://codeforces.com/problemset/problem/471/D)
    -   进阶：[洛谷 P2580 -
        于是他错误的点名开始了](https://www.luogu.com.cn/problem/P2580)；[CF
        126B -
        Password](https://codeforces.com/problemset/problem/126/B)
    -   拓展：[CF 432D - Prefixes and
        Suffixes](https://codeforces.com/problemset/problem/432/D)
    -   牛客补充：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：中频（定性）；精确次数待统计。
-   **关联**：[Z 函数](#242-进阶字符串) · [AC 自动机](#242-进阶字符串) ·
    [后缀数组](#242-进阶字符串)

------------------------------------------------------------------------

# 2. 银牌进阶层 Silver

## 2.1 进阶数据结构

### 2.1.1 离散化与差分

-   **用途**：把稀疏的大值域映射为连续下标；压缩坐标后使用数组、BIT、线段树。
-   **最简单实现**：复制、排序、去重；用 `lower_bound` 找映射位置。
-   **C++ 模板**

``` cpp
vector<long long> xs = values;
sort(xs.begin(), xs.end());
xs.erase(unique(xs.begin(), xs.end()), xs.end());
int id(long long x) {
    return lower_bound(xs.begin(), xs.end(), x) - xs.begin();
}
```

-   **题目**：经典 [洛谷
    P1908](https://www.luogu.com.cn/problem/P1908)；进阶 [洛谷
    P1955](https://www.luogu.com.cn/problem/P1955)；拓展 [CF 121E -
    Lucky Array](https://codeforces.com/problemset/problem/121/E)。
-   **牛客**：[牛客题库](https://www.nowcoder.com/exam/oj)（按"离散化 /
    树状数组"筛选）。
-   **考频**：中高频（定性）；精确次数待统计。
-   **关联**：[Fenwick](#113-树状数组-fenwick) ·
    [线段树](#212-线段树与懒标记) · [扫描线](#331-计算几何与扫描线)

### 2.1.2 线段树与懒标记

-   **用途**：动态维护区间信息；区间求和/最大值/最小值；单点修改、区间修改。
-   **最简单实现**：节点保存区间聚合值；`pull`
    合并子节点；懒标记记录尚未下传的区间更新。
-   **C++ 模板（区间加 + 区间和）**

``` cpp
struct SegTree {
    int n;
    vector<long long> sum, lazy;
    SegTree(int n) : n(n), sum(4*n), lazy(4*n) {}
    void apply(int p, int l, int r, long long v) {
        sum[p] += (r-l) * v;
        lazy[p] += v;
    }
    void push(int p, int l, int r) {
        if (!lazy[p] || r-l==1) return;
        int m=(l+r)/2;
        apply(p*2,l,m,lazy[p]);
        apply(p*2+1,m,r,lazy[p]);
        lazy[p]=0;
    }
    void add(int p,int l,int r,int ql,int qr,long long v) {
        if (qr<=l || r<=ql) return;
        if (ql<=l && r<=qr) return apply(p,l,r,v);
        push(p,l,r);
        int m=(l+r)/2;
        add(p*2,l,m,ql,qr,v);
        add(p*2+1,m,r,ql,qr,v);
        sum[p]=sum[p*2]+sum[p*2+1];
    }
    long long query(int p,int l,int r,int ql,int qr) {
        if (qr<=l || r<=ql) return 0;
        if (ql<=l && r<=qr) return sum[p];
        push(p,l,r);
        int m=(l+r)/2;
        return query(p*2,l,m,ql,qr)+query(p*2+1,m,r,ql,qr);
    }
};
```

-   **题目**
    -   经典：[洛谷 P3372 - 线段树
        1](https://www.luogu.com.cn/problem/P3372)；[洛谷 P3373 - 线段树
        2](https://www.luogu.com.cn/problem/P3373)
    -   进阶：[CF 52C - Circular
        RMQ](https://codeforces.com/problemset/problem/52/C)；[CF edu
        segment tree
        标签题](https://codeforces.com/problemset?tags=data%20structures)
    -   拓展：[CF 620E - New Year
        Tree](https://codeforces.com/problemset/problem/620/E)
    -   牛客：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：高频（定性）；精确次数待统计。
-   **关联**：[Fenwick](#113-树状数组-fenwick) ·
    [可持久化线段树](#311-可持久化数据结构) ·
    [线段树合并](#311-可持久化数据结构)

### 2.1.3 RMQ、单调栈与单调队列

-   **用途**：静态区间最值查询；求每个元素左右第一个更大/更小元素；滑动窗口最值。
-   **最简单实现**：RMQ 用 ST 表预处理 `O(n log n)`、查询
    `O(1)`；单调结构保持栈/队列元素单调。
-   **C++ 模板（单调栈求左侧最近更小元素）**

``` cpp
vector<int> st, leftLess(n, -1);
for (int i = 0; i < n; ++i) {
    while (!st.empty() && a[st.back()] >= a[i]) st.pop_back();
    if (!st.empty()) leftLess[i] = st.back();
    st.push_back(i);
}
```

-   **题目**：经典 [洛谷 P5788 -
    单调栈](https://www.luogu.com.cn/problem/P5788)；进阶 [洛谷 P1886 -
    滑动窗口](https://www.luogu.com.cn/problem/P1886)；拓展 [CF 1195E -
    OpenStreetMap](https://codeforces.com/problemset/problem/1195/E)。
-   **牛客**：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：中高频（定性）；精确次数待统计。
-   **关联**：[线段树](#212-线段树与懒标记) ·
    [双指针](#111-排序二分查找与二分答案) ·
    [RMQ](#213-rmq单调栈与单调队列)

### 2.1.4 可撤销并查集

-   **用途**：离线分治、时间线段树、动态连通性；需要回滚合并状态而不是永久修改。
-   **最简单实现**：通常不做路径压缩；按大小合并；每次修改前记录历史，回滚到某个历史长度。
-   **C++ 模板**

``` cpp
struct RollbackDSU {
    vector<int> p, sz;
    vector<pair<int,int>> hist;
    RollbackDSU(int n): p(n), sz(n,1) { iota(p.begin(),p.end(),0); }
    int find(int x) { while (p[x] != x) x = p[x]; return x; }
    int snapshot() const { return (int)hist.size(); }
    bool unite(int a,int b) {
        a=find(a); b=find(b);
        if(a==b) { hist.push_back({-1,-1}); return false; }
        if(sz[a]<sz[b]) swap(a,b);
        hist.push_back({a,b});
        p[b]=a; sz[a]+=sz[b];
        return true;
    }
    void rollback(int s) {
        while((int)hist.size()>s) {
            auto [a,b]=hist.back(); hist.pop_back();
            if(a==-1) continue;
            p[b]=b; sz[a]-=sz[b];
        }
    }
};
```

-   **题目**：经典 [洛谷
    P1196](https://www.luogu.com.cn/problem/P1196)（并查集扩展）；进阶
    [洛谷 P5787 -
    二分图/时间分治相关训练](https://www.luogu.com.cn/problem/P5787)；拓展
    [CF 1140F - Extending Set of
    Points](https://codeforces.com/problemset/problem/1140/F)。
-   **牛客**：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：低频 / 专题；精确次数待统计。
-   **关联**：[DSU](#114-并查集-dsu) · [分治](#232-树形dp与状压dp) ·
    [线段树分治](#311-可持久化数据结构)

## 2.2 进阶图论

### 2.2.1 强连通分量 SCC

-   **用途**：有向图中互相可达的极大点集；缩点后得到
    DAG，处理依赖、环、可达性与 DAG DP。
-   **最简单实现**：Tarjan DFS 维护 `dfn/low` 和栈；当 `dfn[u]==low[u]`
    时弹出一个 SCC。
-   **C++ 模板（Tarjan）**

``` cpp
int timer=0, cnt=0;
vector<int> dfn(n), low(n), comp(n,-1), stk;
vector<char> in(n);
function<void(int)> tarjan = [&](int u) {
    dfn[u]=low[u]=++timer;
    stk.push_back(u); in[u]=1;
    for(int v:g[u]) {
        if(!dfn[v]) tarjan(v), low[u]=min(low[u],low[v]);
        else if(in[v]) low[u]=min(low[u],dfn[v]);
    }
    if(dfn[u]==low[u]) {
        while(true) {
            int v=stk.back(); stk.pop_back(); in[v]=0;
            comp[v]=cnt;
            if(v==u) break;
        }
        ++cnt;
    }
};
```

-   **题目**
    -   经典：[洛谷 P3387 -
        缩点](https://www.luogu.com.cn/problem/P3387)
    -   进阶：[CF 427C -
        Checkposts](https://codeforces.com/problemset/problem/427/C)；[CF
        1213F - Unstable String
        Sort](https://codeforces.com/problemset/problem/1213/F)
    -   拓展：[CF 1494F - Delete The
        Edges](https://codeforces.com/problemset/problem/1494/F)
    -   牛客：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：中高频（定性）；精确次数待统计。
-   **关联**：[割点与桥](#221-强连通分量-scc) · [2-SAT](#222-2-sat) ·
    [DAG DP](#232-树形dp与状压dp)

### 2.2.2 2-SAT

-   **用途**：每个变量只能取真/假，约束可转化为二元蕴含；判断是否存在满足所有约束的赋值。
-   **最简单实现**：变量 `x` 拆成 `x` 与 `¬x`；每个子句 `(a∨b)` 加边
    `¬a→b`、`¬b→a`；跑 SCC，若 `x` 与 `¬x` 同 SCC 则无解。
-   **C++ 模板**

``` cpp
// literal id: 2*i means x_i=true, 2*i+1 means false
vector<vector<int>> g(2*n);
auto addOr = [&](int a,int b) {
    g[a^1].push_back(b);
    g[b^1].push_back(a);
};
// run SCC on 2*n nodes; contradiction if comp[2*i] == comp[2*i+1]
```

-   **题目**：经典 [洛谷 P4782 -
    2-SAT](https://www.luogu.com.cn/problem/P4782)；进阶 [CF
    1722F](https://codeforces.com/problemset/problem/1722/F)（逻辑约束建模）；拓展
    [洛谷 2-SAT 题单](https://www.luogu.com.cn/training/list)。
-   **牛客**：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：中频 / 专题；精确次数待统计。
-   **关联**：[SCC](#221-强连通分量-scc) ·
    [图建模](#121-图遍历与最小生成树)

### 2.2.3 树与 LCA、树链剖分 HLD

-   **用途**：LCA 求树上两点最近公共祖先；HLD 把树路径拆成 `O(log n)`
    条连续区间，配合线段树维护路径信息。
-   **最简单实现**：倍增预处理祖先表；HLD 先求重儿子，再分解链并维护 DFS
    序。
-   **C++ 模板（倍增 LCA）**

``` cpp
int LOG = 20;
vector<vector<int>> up(LOG, vector<int>(n));
vector<int> dep(n);
function<void(int,int)> dfs = [&](int u,int p) {
    up[0][u]=p;
    for(int k=1;k<LOG;k++) up[k][u]=up[k-1][up[k-1][u]];
    for(int v:g[u]) if(v!=p) dep[v]=dep[u]+1, dfs(v,u);
};
auto lca = [&](int a,int b) {
    if(dep[a]<dep[b]) swap(a,b);
    for(int k=LOG-1;k>=0;k--) if(dep[up[k][a]]>=dep[b]) a=up[k][a];
    if(a==b) return a;
    for(int k=LOG-1;k>=0;k--) if(up[k][a]!=up[k][b]) a=up[k][a],b=up[k][b];
    return up[0][a];
};
```

-   **题目**
    -   经典：[洛谷 P3379 -
        最近公共祖先](https://www.luogu.com.cn/problem/P3379)
    -   进阶：[洛谷 P2590 -
        树的统计](https://www.luogu.com.cn/problem/P2590)；[CF 609E -
        Minimum spanning tree for each
        edge](https://codeforces.com/problemset/problem/609/E)
    -   拓展：[洛谷 P2486 -
        染色](https://www.luogu.com.cn/problem/P2486)
    -   牛客：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：中高频（定性）；精确次数待统计。
-   **关联**：[线段树](#212-线段树与懒标记) · [树形
    DP](#232-树形dp与状压dp) · [LCT](#311-可持久化数据结构)

### 2.2.4 二分图匹配与网络流入门

-   **用途**：二分图匹配解决两侧对象的一对一分配；最大流解决容量网络中的最大可传输量。
-   **最简单实现**：匈牙利算法递归寻找增广路；Dinic 用 BFS 分层图 + DFS
    阻塞流。
-   **C++ 模板（匈牙利算法）**

``` cpp
vector<vector<int>> g(n);
vector<int> match(m,-1), vis(m);
int stamp=0;
function<bool(int)> dfs = [&](int u) {
    for(int v:g[u]) if(vis[v]!=stamp) {
        vis[v]=stamp;
        if(match[v]==-1 || dfs(match[v])) {
            match[v]=u; return true;
        }
    }
    return false;
};
int ans=0;
for(int u=0;u<n;u++) { ++stamp; ans += dfs(u); }
```

-   **题目**：经典 [洛谷 P3386 -
    二分图最大匹配](https://www.luogu.com.cn/problem/P3386)；进阶 [洛谷
    P3376 - 网络最大流](https://www.luogu.com.cn/problem/P3376)；拓展
    [CF 546E - Soldier and
    Traveling](https://codeforces.com/problemset/problem/546/E)。
-   **牛客**：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：匹配中频、网络流中高频（定性）；精确次数待统计。
-   **关联**：[SCC](#221-强连通分量-scc) · [最小费用流](#222-网络流) ·
    [二分图建模](#222-网络流)

### 2.2.5 网络流

-   **用途**：最大流处理容量约束；最小费用最大流处理单位流量带费用的分配/运输。
-   **最简单实现**：Dinic 在残量网络中不断寻找阻塞流；费用流常用势能 +
    Dijkstra 加速最短增广路。
-   **C++ 模板骨架（Dinic）**

``` cpp
struct Dinic {
    struct E { int to, rev; long long cap; };
    int n;
    vector<vector<E>> g;
    vector<int> level, it;
    Dinic(int n): n(n), g(n), level(n), it(n) {}
    void addEdge(int u,int v,long long c) {
        E a{v,(int)g[v].size(),c}, b{u,(int)g[u].size(),0};
        g[u].push_back(a); g[v].push_back(b);
    }
    bool bfs(int s,int t) {
        fill(level.begin(),level.end(),-1);
        queue<int> q; q.push(s); level[s]=0;
        while(!q.empty()) {
            int u=q.front();q.pop();
            for(auto &e:g[u]) if(e.cap>0 && level[e.to]<0)
                level[e.to]=level[u]+1,q.push(e.to);
        }
        return level[t]>=0;
    }
    long long dfs(int u,int t,long long f) {
        if(u==t) return f;
        for(int &i=it[u];i<(int)g[u].size();++i) {
            E &e=g[u][i];
            if(e.cap && level[e.to]==level[u]+1) {
                long long x=dfs(e.to,t,min(f,e.cap));
                if(x) { e.cap-=x; g[e.to][e.rev].cap+=x; return x; }
            }
        }
        return 0;
    }
    long long flow(int s,int t) {
        long long ans=0, f;
        while(bfs(s,t)) {
            fill(it.begin(),it.end(),0);
            while((f=dfs(s,t,LLONG_MAX))) ans+=f;
        }
        return ans;
    }
};
```

-   **题目**：经典 [洛谷
    P3376](https://www.luogu.com.cn/problem/P3376)；进阶 [洛谷 P4016 -
    负载平衡问题](https://www.luogu.com.cn/problem/P4016)；拓展 [CF
    546E](https://codeforces.com/problemset/problem/546/E)。
-   **牛客**：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：中频 / 专题；精确次数待统计。
-   **关联**：[二分图匹配](#224-二分图匹配与网络流入门) ·
    [最短路](#122-最短路) · [费用流](#222-网络流)

## 2.3 进阶 DP 与算法设计

### 2.3.1 区间 DP、树形 DP 与状压 DP

-   **用途**：区间 DP 合并相邻子区间；树形 DP 在子树间合并状态；状压 DP
    用 bitmask 表示小规模集合状态。
-   **最简单实现**：先定义状态含义，再枚举最后一步/根节点/子集转移；确认复杂度与状态规模。
-   **C++ 模板（区间 DP 骨架）**

``` cpp
for (int len=2; len<=n; ++len)
    for (int l=0; l+len<=n; ++l) {
        int r=l+len-1;
        dp[l][r]=INF;
        for (int k=l; k<r; ++k)
            dp[l][r]=min(dp[l][r], dp[l][k]+dp[k+1][r]+cost(l,k,r));
    }
```

-   **题目**：经典 [洛谷 P1775 -
    石子合并（弱化版）](https://www.luogu.com.cn/problem/P1775)；进阶
    [CF 607B -
    Zuma](https://codeforces.com/problemset/problem/607/B)；拓展 [CF
    152E - Garden](https://codeforces.com/problemset/problem/152/E)。
-   **牛客**：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：中高频（定性）；精确次数待统计。
-   **关联**：[线性 DP](#131-线性-dp背包与-lis) · [DAG
    DP](#221-强连通分量-scc) · [DP 优化](#332-高级-dp-优化)

### 2.3.2 莫队、分治与 CDQ

-   **用途**：莫队离线处理区间询问；CDQ
    分治解决带时间/偏序关系的离线贡献；整体二分处理可二分答案的批量询问。
-   **最简单实现**：把询问排序成移动代价较小的顺序，维护当前区间答案；CDQ
    按一维分治、另一维排序并用 BIT 统计。
-   **C++ 模板（普通莫队框架）**

``` cpp
struct Query { int l,r,id; };
int B;
sort(q.begin(),q.end(),[&](auto a,auto b){
    if(a.l/B!=b.l/B) return a.l<b.l;
    return (a.l/B)&1 ? a.r>b.r : a.r<b.r;
});
int L=0,R=-1;
for(auto qu:q) {
    while(L>qu.l) add(--L);
    while(R<qu.r) add(++R);
    while(L<qu.l) del(L++);
    while(R>qu.r) del(R--);
    ans[qu.id]=getAnswer();
}
```

-   **题目**：经典 [洛谷 P3901 -
    数列找不同](https://www.luogu.com.cn/problem/P3901)；进阶 [洛谷
    P1494 - \[国家集训队\]小 Z
    的袜子](https://www.luogu.com.cn/problem/P1494)；拓展 [洛谷 CDQ
    分治题单](https://www.luogu.com.cn/training/list)。
-   **牛客**：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：低频 / 专题；精确次数待统计。
-   **关联**：[Fenwick](#113-树状数组-fenwick) ·
    [离散化](#211-离散化与差分) · [可撤销并查集](#213-可撤销并查集)

## 2.4 进阶数学与字符串

### 2.4.1 进阶数论

-   **范围**：扩展欧几里得、逆元、欧拉函数、莫比乌斯反演、CRT、中国剩余定理、Lucas、Miller--Rabin、Pollard--Rho。
-   **用途**：线性丢番图方程、模意义除法、互质计数、整除函数反演、大整数分解与素性测试。
-   **最简单实现**：`exgcd` 求 `ax+by=gcd(a,b)`；逆元在模数为质数且 `a`
    非零时用 `a^(p-2)`；Miller--Rabin 用随机/确定底数做强伪素数测试。
-   **C++ 模板（exgcd）**

``` cpp
long long exgcd(long long a,long long b,long long& x,long long& y) {
    if(!b) { x=1; y=0; return a; }
    long long x1,y1;
    long long g=exgcd(b,a%b,x1,y1);
    x=y1; y=x1-(a/b)*y1;
    return g;
}
```

-   **题目**：经典 [洛谷 P1082 -
    同余方程](https://www.luogu.com.cn/problem/P1082)；进阶 [洛谷
    P1495 - 中国剩余定理](https://www.luogu.com.cn/problem/P1495)；拓展
    [洛谷 P4718 - Pollard-Rho](https://www.luogu.com.cn/problem/P4718)。
-   **牛客**：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：数论基础高频；反演与大数分解中低频 /
    专题；精确次数待统计。
-   **关联**：[快速幂](#141-gcd快速幂素数筛与组合数基础) ·
    [组合数](#241-进阶数论) · [NTT](#333-多项式与生成函数)

### 2.4.2 进阶字符串

-   **范围**：Z 函数、Manacher、后缀数组 SA、LCP、后缀自动机 SAM、AC
    自动机、回文自动机 PAM。
-   **用途**：线性求前缀匹配；最长回文子串；后缀排序与子串比较；多模式串匹配；统计不同子串与回文子串。
-   **最简单实现**：Z 算法维护最右匹配区间；Manacher
    在字符间插入分隔符；SA 倍增排序后缀；SAM 在线扩展状态并维护 suffix
    link。
-   **C++ 模板（Manacher 核心）**

``` cpp
string t = "^#";
for(char c:s) t += c, t += '#';
t += '$';
vector<int> p(t.size());
int c=0,r=0;
for(int i=1;i+1<(int)t.size();++i) {
    if(i<r) p[i]=min(r-i,p[2*c-i]);
    while(t[i+1+p[i]]==t[i-1-p[i]]) ++p[i];
    if(i+p[i]>r) c=i,r=i+p[i];
}
```

-   **题目**：经典 [洛谷 P3805 -
    Manacher](https://www.luogu.com.cn/problem/P3805)；进阶 [洛谷
    P3809 - 后缀排序](https://www.luogu.com.cn/problem/P3809)；拓展
    [洛谷 P4555 -
    最长双回文串](https://www.luogu.com.cn/problem/P4555)、[洛谷 P4248 -
    SAM](https://www.luogu.com.cn/problem/P4248)。
-   **牛客**：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：KMP / Trie 中高频；SA / SAM / AC 中频；PAM
    专题；精确次数待统计。
-   **关联**：[KMP](#142-kmptrie-与字符串哈希) ·
    [SCC](#221-强连通分量-scc) · [后缀自动机](#242-进阶字符串)

------------------------------------------------------------------------

# 3. 金牌拓展层 Gold

> 金牌章节是高阶能力拓展，不代表每场 ICPC / CCPC
> 金牌队伍都必须掌握全部内容。建议先掌握银牌核心，再根据区域赛风格和个人薄弱项选择专题。

## 3.1 高级数据结构

### 3.1.1 可持久化数据结构

-   **用途**：保留历史版本，支持查询过去某一版本；主席树常用于区间第 k
    小、历史版本统计。
-   **最简单实现**：每次修改只复制被访问的根到叶路径，其余节点共享；版本由根指针表示。
-   **C++ 模板（可持久化线段树节点池骨架）**

``` cpp
struct Node { int l=0,r=0,sum=0; };
vector<Node> tr(1);
int clone(int p) { tr.push_back(tr[p]); return (int)tr.size()-1; }
int update(int old,int l,int r,int x) {
    int p=clone(old);
    ++tr[p].sum;
    if(r-l==1) return p;
    int m=(l+r)/2;
    if(x<m) tr[p].l=update(tr[old].l,l,m,x);
    else tr[p].r=update(tr[old].r,m,r,x);
    return p;
}
```

-   **题目**：经典 [洛谷 P3834 - 可持久化线段树
    2](https://www.luogu.com.cn/problem/P3834)；进阶 [洛谷 P3919 -
    可持久化数组](https://www.luogu.com.cn/problem/P3919)；拓展 [CF
    恒定题库搜索](https://codeforces.com/problemset?tags=persistent%20data%20structures)。
-   **牛客**：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：低频 / 专题；精确次数待统计。
-   **关联**：[线段树](#212-线段树与懒标记) ·
    [离散化](#211-离散化与差分) · [主席树](#311-可持久化数据结构)

### 3.1.2 平衡树：Splay / Treap

-   **用途**：动态维护有序集合，支持插入、删除、排名、第 k
    小、前驱后继。
-   **最简单实现**：Treap 用随机优先级维护 BST + Heap 性质；Splay
    通过旋转把访问节点伸展到根。
-   **C++ 模板（Treap 操作骨架）**

``` cpp
struct Node { int l=0,r=0,key=0,pri=0,sz=1; };
int size(int p){ return p?tr[p].sz:0; }
void pull(int p){ tr[p].sz=1+size(tr[p].l)+size(tr[p].r); }
// split / merge / insert / erase are implemented using key and priority.
```

-   **题目**：经典 [洛谷 P3369 -
    普通平衡树](https://www.luogu.com.cn/problem/P3369)；进阶 [洛谷
    P6136 -
    普通平衡树（数据加强版）](https://www.luogu.com.cn/problem/P6136)；拓展
    [CF 平衡树标签题](https://codeforces.com/problemset?tags=trees)。
-   **牛客**：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：低频 / 专题；精确次数待统计。
-   **关联**：[线段树](#212-线段树与懒标记) ·
    [可持久化结构](#311-可持久化数据结构)

### 3.1.3 Link-Cut Tree（LCT）

-   **用途**：动态森林，支持连接、断开、查询路径信息；边动态变化时维护树路径。
-   **最简单实现**：用 Splay
    表示辅助树；`access`、`makeroot`、`findroot`、`link`、`cut`
    完成动态树操作。
-   **C++ 模板（接口骨架）**

``` cpp
struct LCT {
    struct Node { int ch[2]{}, fa=0; bool rev=false; };
    vector<Node> t;
    bool isRoot(int x) {
        int f=t[x].fa;
        return !f || (t[f].ch[0]!=x && t[f].ch[1]!=x);
    }
    void pushRev(int x) {
        if(!x) return;
        swap(t[x].ch[0],t[x].ch[1]); t[x].rev^=1;
    }
    // pushDown / rotate / splay / access / makeroot / findroot / link / cut
};
```

-   **题目**：经典 [洛谷 P3690 -
    动态树](https://www.luogu.com.cn/problem/P3690)；进阶 [洛谷 P1501 -
    动态树（LCT）](https://www.luogu.com.cn/problem/P1501)；拓展 [洛谷
    LCT 题单](https://www.luogu.com.cn/training/list)。
-   **牛客**：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：低频 / 专题；精确次数待统计。
-   **关联**：[Splay](#312-平衡树splay-treap) ·
    [树链剖分](#223-树与-lca树链剖分-hld)

## 3.2 高级图论

### 3.2.1 一般图最大权匹配 / Blossom

-   **用途**：一般图（不要求二分图）最大匹配或带权匹配；处理奇环导致的增广路收缩。
-   **最简单实现**：寻找增广路；遇到花（奇环）时收缩为一个点，再继续搜索。
-   **C++ 模板**：建议作为独立算法模块引入经过验证的 Blossom
    实现；必须覆盖奇环、重边、自环和非完美匹配测试。不要在未验证的情况下直接使用网络流替代。
-   **题目**：经典/进阶/拓展建议从
    [洛谷一般图匹配题单](https://www.luogu.com.cn/training/list) 与
    [Codeforces matching
    标签](https://codeforces.com/problemset?tags=matching) 中按 Blossom
    标注筛选；牛客：[牛客题库](https://www.nowcoder.com/exam/oj)。
-   **考频**：低频 / 专题；精确次数待统计。
-   **关联**：[二分图匹配](#224-二分图匹配与网络流入门) ·
    [网络流](#225-网络流)

### 3.2.2 高级网络流、最小割与最小割树

-   **用途**：最小割刻画网络脆弱性；最小割树（Gomory--Hu
    Tree）回答无向图任意两点最小割值。
-   **最简单实现**：重复运行最大流，依据残量网络可达集更新割树结构。
-   **C++ 模板**：复用经过验证的 Dinic；最小割树额外实现 Gomory--Hu
    构造，不建议把构造逻辑与 Dinic 混写。
-   **题目**：经典 [洛谷 P1345 -
    奶牛的电信](https://www.luogu.com.cn/problem/P1345)；进阶 [CF 343E -
    Pumping
    Stations](https://codeforces.com/problemset/problem/343/E)；拓展
    [最小割树专题检索](https://codeforces.com/problemset?tags=flows)；牛客：[牛客题库](https://www.nowcoder.com/exam/oj)。
-   **考频**：低频 / 专题；精确次数待统计。
-   **关联**：[Dinic](#225-网络流) ·
    [最小割](#322-高级网络流最小割与最小割树)

## 3.3 高级 DP、数学与计算几何

### 3.3.1 高级 DP 优化

-   **范围**：斜率优化、决策单调性、四边形不等式、WQS 二分、插头 DP、SOS
    DP、轮廓线 DP。
-   **用途**：把朴素高复杂度转化为单调队列、凸包、分治或状态压缩优化。
-   **最简单实现**：先写出朴素转移；识别转移函数的单调性/凸性/可分性；再证明优化结构成立。
-   **C++ 模板（凸包优化单调斜率骨架）**

``` cpp
struct Line { long long m,b; long long eval(long long x) const { return m*x+b; } };
vector<Line> hull;
// For minimum queries with monotone slopes and monotone x:
// remove the middle line when intersection order is invalid.
```

-   **题目**：经典 [洛谷 P5785 -
    \[SDOI2012\]任务安排](https://www.luogu.com.cn/problem/P5785)；进阶
    [洛谷 P3195 -
    玩具装箱](https://www.luogu.com.cn/problem/P3195)；拓展 [洛谷 DP
    优化题单](https://www.luogu.com.cn/training/list)。
-   **牛客**：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：优化 DP 中低频 / 专题；精确次数待统计。
-   **关联**：[线性 DP](#131-线性-dp背包与-lis) ·
    [分治](#232-莫队分治与-cdq) · [凸包](#331-计算几何与扫描线)

### 3.3.2 多项式与生成函数

-   **范围**：FFT / NTT、多项式乘法、求逆、求导、积分、ln /
    exp、形式幂级数、生成函数。
-   **用途**：快速卷积、组合计数、递推加速与大规模系数运算。
-   **最简单实现**：把序列视为多项式；NTT
    在适配模数下进行快速数论变换，点值相乘后逆变换。
-   **C++ 模板（NTT 主流程骨架）**

``` cpp
// NTT requires a suitable prime modulus and primitive root.
// 1) bit-reversal permutation
// 2) iterative butterfly stages with roots of unity
// 3) inverse transform and multiply by inv(n)
// Use a tested implementation for production training.
```

-   **题目**：经典 [洛谷 P1919 - A\*B
    Problem（FFT）](https://www.luogu.com.cn/problem/P1919)；进阶 [洛谷
    P3803 -
    多项式乘法（FFT）](https://www.luogu.com.cn/problem/P3803)；拓展
    [洛谷 P6097 -
    【模板】子集卷积](https://www.luogu.com.cn/problem/P6097)。
-   **牛客**：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：低频 / 专题；精确次数待统计。
-   **关联**：[组合数](#241-进阶数论) ·
    [快速幂](#141-gcd快速幂素数筛与组合数基础) · [DP
    优化](#331-高级-dp-优化)

### 3.3.3 计算几何与扫描线

-   **范围**：向量叉积、点线关系、凸包、旋转卡壳、扫描线、半平面交、圆与多边形、三维几何。
-   **用途**：平面位置关系、面积/周长、最远点对、覆盖面积、几何可行性。
-   **最简单实现**：用叉积判断转向与相对位置；凸包排序后维护上下链；扫描线把二维事件转为一维区间维护。
-   **C++ 模板（叉积与凸包骨架）**

``` cpp
struct Point {
    long long x,y;
    bool operator<(const Point& o) const {
        return x==o.x ? y<o.y : x<o.x;
    }
};
long long cross(Point a,Point b,Point c) {
    return (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);
}
// Monotone chain: sort points; build lower and upper hull,
// popping while cross <= 0 (adapt for collinear-point policy).
```

-   **题目**：经典 [洛谷 P2742 -
    二维凸包](https://www.luogu.com.cn/problem/P2742)；进阶 [洛谷
    P5490 - 扫描线](https://www.luogu.com.cn/problem/P5490)；拓展 [洛谷
    P3829 -
    题目相关计算几何训练](https://www.luogu.com.cn/problem/P3829)。
-   **牛客**：[牛客题库](https://www.nowcoder.com/exam/oj)
-   **考频**：基础几何中频；高级几何低频 / 专题；精确次数待统计。
-   **关联**：[线段树](#212-线段树与懒标记) ·
    [排序](#111-排序二分查找与二分答案) · [凸包优化
    DP](#331-高级-dp-优化)

------------------------------------------------------------------------

# 4. 题目链接索引

## 4.1 题库入口

-   [Codeforces Problemset](https://codeforces.com/problemset)
-   [Codeforces Gym](https://codeforces.com/gyms)
-   [牛客竞赛题库](https://www.nowcoder.com/exam/oj)
-   [牛客竞赛](https://ac.nowcoder.com/)
-   [洛谷题库](https://www.luogu.com.cn/problem/list)
-   [洛谷题单](https://www.luogu.com.cn/training/list)
-   [ICPC Problem Archive](https://icpc.io/archive/)

## 4.2 题目等级建议

  ------------------------------------------------------------------------------------------
  级别                    选题标准                                   在 MomoCode
                                                                     中的训练任务
  ----------------------- ------------------------------------------ -----------------------
  经典例题                单一知识点、模型明显、约束标准             识别题 + 模板填空

  进阶例题                需要建模、变形或组合一个辅助知识点         独立实现 + 解释复杂度

  拓展例题                多知识点组合、边界复杂、证明或优化要求高   限时完整复现 + 错误定位
  ------------------------------------------------------------------------------------------

**关于牛客链接：**
牛客题库的题目入口与专题编排会调整，本版先提供稳定题库入口；正式发布时应将具体牛客题号、比赛场次和题目标题补齐，避免编造题号。可按知识点检索题目后写入
`problem_catalog`。

------------------------------------------------------------------------

# 5. 与 jiangly 模板 PDF 的对应关系

用户提供的《【jiangly】算法模板.pdf》（WIDA，2024-10-07）是**模板代码来源**，而不是
ICPC / CCPC 考频数据来源。本手册按知识点做了训练分层；PDF
中的模板可以作为实现参考。

  ------------------------------------------------------------------------------------------------------------------------------------------
  PDF 章节 / 模板                                                                本手册归属              备注
  ------------------------------------------------------------------------------ ----------------------- -----------------------------------
  `__int128`、常用库函数、整数/实数二分                                          铜牌基础 / 工具         二分也可能作为银牌复杂题子过程

  SCC、EBCC、KM、一般图带花树、2-SAT、最大流、费用流、HLD                        银牌 / 金牌专题         Blossom、KM、费用流按题目要求进阶

  快速幂、欧拉筛、莫比乌斯、exgcd、欧拉函数、组合数、Miller-Rabin、Pollard-Rho   铜牌基础 + 银牌进阶     数论难度跨度较大

  几何、凸包、多项式、NTT、生成函数、Simpson、矩阵、高斯消元                     银牌进阶 + 金牌拓展     专题性强

  Fenwick、DSU、可撤销                                                           铜牌基础 + 银牌 + 金牌  数据结构按操作复杂度分层
  DSU、SegmentTree、LazySegmentTree、RMQ、Splay、Frac、Basis、BigInt、LCT                                

  Manacher、Z、SA、SAM、PAM、AC、Hash、LCP、Trie、KMP                            铜牌基础 + 银牌进阶     字符串自动机通常属于进阶专题
  ------------------------------------------------------------------------------------------------------------------------------------------

**重要**：本手册中的短模板是教学骨架，不保证逐行等同于 PDF
原始代码。需要复现 PDF 时，应回到 PDF
对应页码，保留原始接口、边界约定和实现细节。

------------------------------------------------------------------------

# 6. MomoCode 数据化建议

## 6.1 每个知识点的数据结构

``` json
{
  "slug": "fenwick-tree",
  "name": "树状数组",
  "aliases": ["Fenwick Tree", "BIT"],
  "tier": ["bronze", "silver"],
  "purpose": ["单点修改", "前缀和查询", "逆序对"],
  "complexity": {
    "update": "O(log n)",
    "query": "O(log n)"
  },
  "template_language": "cpp17",
  "template_version": "1.0.0",
  "contest_frequency": {
    "icpc": null,
    "ccpc": null,
    "period": "2015-2025",
    "scope": "待定义赛事范围",
    "status": "unverified"
  },
  "related": ["segment-tree", "coordinate-compression", "inversion-count"],
  "problems": []
}
```

## 6.2 例题数据结构

``` json
{
  "platform": "luogu",
  "problem_id": "P3374",
  "title": "树状数组 1",
  "url": "https://www.luogu.com.cn/problem/P3374",
  "knowledge": ["fenwick-tree"],
  "difficulty": "classic",
  "role": "template-introduction",
  "verified": false
}
```

## 6.3 考频统计数据结构

``` json
{
  "knowledge_slug": "scc",
  "contest_family": "ICPC",
  "period_start": 2015,
  "period_end": 2025,
  "contest_scope": ["regional", "world-finals"],
  "contest_occurrences": null,
  "problem_occurrences": null,
  "multi_tag": true,
  "source_dataset": null,
  "method_version": "1.0",
  "status": "待统计"
}
```

## 6.4 建议的自动统计流程

1.  收集官方赛事题目清单、题面、官方题解和可验证代码。
2.  统一赛事元数据：赛事系列、年份、赛区、场次、题号。
3.  对每道题建立多标签知识点标注；允许一题多个标签。
4.  对不确定标签设为 `needs_review`，由人工复核。
5.  同时输出"出现过该知识点的赛事数"和"涉及该知识点的题目数"。
6.  按赛事范围和年份输出筛选结果；不能用题目总数代替赛事次数。
7.  每年更新一次数据集与统计版本。

## 6.5 建议的 MomoCode 训练闭环

``` text
知识点卡片
   ↓
算法识别（判断何时使用）
   ↓
模板填空（补齐关键函数）
   ↓
完整复现（从空白写出）
   ↓
经典例题（单知识点）
   ↓
进阶例题（建模 + 组合）
   ↓
拓展例题（多知识点 / 优化）
   ↓
间隔复习（错题原因 + 下次复习时间）
```

------------------------------------------------------------------------

## 版本备注

-   本版覆盖常见 ICPC / CCPC 训练主干与用户提供的 jiangly
    模板目录中的主要专题。
-   题目链接用于建立训练入口；题目难度会因个人基础与比赛背景变化。
-   牛客具体题号尚未逐题核验，因此使用平台入口而非虚构题目。
-   ICPC / CCPC
    精确考频尚未从完整历史题库逐题标注，本版只提供定性频率与统计方案。
-   代码模板中的 `check`、部分高级数据结构操作、NTT
    完整变换等为接口/骨架，需要在对应专题练习中补全与验证。
