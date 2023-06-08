const SCORE_COEFFICIENT_TABLE = [
    [0, 0, 'd'],
    [50, 8, 'c'],
    [60, 9.6, 'b'],
    [70, 11.2, 'bb'],
    [75, 12.0, 'bbb'],
    [80, 13.6, 'a'],
    [90, 15.2, 'aa'],
    [94, 16.8, 'aaa'],
    [97, 20, 's'],
    [98, 20.3, 'sp'],
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

    ra(ds) {
        return Math.floor(this.c * ds * Math.min(100.5, this.a) / 100);
    }
}

module.exports = ScoreCoefficient
