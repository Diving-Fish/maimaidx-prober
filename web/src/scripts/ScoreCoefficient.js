const SCORE_COEFFICIENT_TABLE = [
    [0, 0, 'd'],
    [10, 1.6, 'd'],
    [20, 3.2, 'd'],
    [30, 4.8, 'd'],
    [40, 6.4, 'd'],
    [50, 8.0, 'c'],
    [60, 9.6, 'b'],
    [70, 11.2, 'bb'],
    [75, 12.0, 'bbb'],
    [79.9999, 12.8, 'bbb'],
    [80, 13.6, 'a'],
    [90, 15.2, 'aa'],
    [94, 16.8, 'aaa'],
    [96.9999, 17.6, 's'],
    [97, 20.0, 's'],
    [98, 20.3, 'sp'],
    [98.9999, 20.6, 'sp'],
    [99, 20.8, 'ss'],
    [99.5, 21.1, 'ssp'],
    [99.9999, 21.4, 'ssp'],
    [100, 21.6, 'sss'],
    [100.4999, 22.2, 'sss'],
    [100.5, 22.4, 'sssp']
]

class ScoreCoefficient {
    constructor(achievements) {
        for (let i = 0; i < SCORE_COEFFICIENT_TABLE.length; i++) {
            if (i === SCORE_COEFFICIENT_TABLE.length - 1 || achievements < SCORE_COEFFICIENT_TABLE[i + 1][0]) {
                this.a = achievements
                this.c = SCORE_COEFFICIENT_TABLE[i][1]
                this.r = SCORE_COEFFICIENT_TABLE[i][2]
                this.idx = i
                return
            }
        }
    }

    set_idx(idx) {
        if (this.idx < SCORE_COEFFICIENT_TABLE.length) {
            this.a = SCORE_COEFFICIENT_TABLE[idx][0]
            this.c = SCORE_COEFFICIENT_TABLE[idx][1]
            this.r = SCORE_COEFFICIENT_TABLE[idx][2]
            this.idx = idx
        }
    }

    get_more_ra_local(ds) {
        const ra = this.ra(ds) + 1;
        const ach = Math.ceil(Math.min(ra * 100 / ds / this.c, 100.5) * 10000) / 10000;
        if (this.idx === SCORE_COEFFICIENT_TABLE.length - 1 || ach < SCORE_COEFFICIENT_TABLE[this.idx + 1][0]) {
            return { ra: ra, achievements: ach };
        }
        return undefined;
    }

    get_table_len() {
        return SCORE_COEFFICIENT_TABLE.length;
    }

    ra(ds) {
        return Math.floor(this.c * ds * Math.min(100.5, this.a) / 100);
    }
}

module.exports = ScoreCoefficient
