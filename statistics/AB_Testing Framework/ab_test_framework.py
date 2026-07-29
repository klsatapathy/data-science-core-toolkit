
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize, proportions_ztest, proportion_confint


class ABTestFramework:
    """Reusable framework for planning and evaluating A/B tests on binary outcomes."""

    def __init__(self, alpha: float = 0.05, power: float = 0.8, seed: int = 42):
        self.alpha = alpha
        self.power = power
        self.rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # 1. Experiment design
    # ------------------------------------------------------------------
    def calculate_sample_size(self, baseline_rate: float, mde: float) -> int:
        """
        Required sample size PER GROUP to detect a change from `baseline_rate`
        to `baseline_rate + mde`, at self.alpha significance and self.power power.

        baseline_rate: expected control-group conversion/retention rate (0-1)
        mde: minimum detectable effect, as an absolute change in rate (e.g. 0.01 = 1pp)
        """
        effect_size = proportion_effectsize(baseline_rate, baseline_rate + mde)
        analysis = NormalIndPower()
        n = analysis.solve_power(effect_size=abs(effect_size), alpha=self.alpha,
                                  power=self.power, ratio=1.0)
        return int(np.ceil(n))

    def minimum_detectable_effect(self, baseline_rate: float, n_per_group: int,
                                   tol: float = 1e-5) -> float:
        """
        Given an available sample size per group, find the smallest absolute
        effect size (MDE) that could be reliably detected at self.power power.
        Solved via binary search since MDE has no closed form here.
        """
        analysis = NormalIndPower()
        low, high = 1e-4, 0.5
        while high - low > tol:
            mid = (low + high) / 2
            effect_size = proportion_effectsize(baseline_rate, baseline_rate + mid)
            achieved_power = analysis.power(effect_size=abs(effect_size), nobs1=n_per_group,
                                             alpha=self.alpha, ratio=1.0)
            if achieved_power < self.power:
                low = mid
            else:
                high = mid
        return round(high, 4)

    # ------------------------------------------------------------------
    # 2. Running the test
    # ------------------------------------------------------------------
    def run_test(self, group_a: pd.Series, group_b: pd.Series) -> dict:
        """
        Two-proportion z-test comparing binary outcome rates between two groups.
        group_a / group_b: boolean or 0/1 series (e.g. df[df.version=='gate_30']['retention_7'])
        """
        count = np.array([group_a.sum(), group_b.sum()])
        nobs = np.array([len(group_a), len(group_b)])

        z_stat, p_val = proportions_ztest(count, nobs)
        ci_a = proportion_confint(count[0], nobs[0], alpha=self.alpha, method='wilson')
        ci_b = proportion_confint(count[1], nobs[1], alpha=self.alpha, method='wilson')

        rate_a, rate_b = count[0] / nobs[0], count[1] / nobs[1]

        return {
            'rate_a': rate_a, 'rate_b': rate_b,
            'ci_a': ci_a, 'ci_b': ci_b,
            'absolute_diff': rate_a - rate_b,
            'relative_diff_pct': (rate_a / rate_b - 1) * 100 if rate_b > 0 else np.nan,
            'z_stat': z_stat, 'p_value': p_val,
            'significant': p_val < self.alpha
        }

    # ------------------------------------------------------------------
    # 3. Bootstrap confidence interval
    # ------------------------------------------------------------------
    def bootstrap_ci(self, group_a: pd.Series, group_b: pd.Series,
                      n_iterations: int = 10000) -> dict:
        """
        Empirical (resampling-based) confidence interval for the difference
        in mean outcome rate between two groups, as a cross-check on the
        formula-based CI from run_test().
        """
        a_arr, b_arr = group_a.to_numpy(), group_b.to_numpy()
        diffs = np.empty(n_iterations)
        for i in range(n_iterations):
            sample_a = self.rng.choice(a_arr, size=len(a_arr), replace=True)
            sample_b = self.rng.choice(b_arr, size=len(b_arr), replace=True)
            diffs[i] = sample_a.mean() - sample_b.mean()

        lower, upper = np.percentile(diffs, [(self.alpha / 2) * 100, (1 - self.alpha / 2) * 100])
        return {
            'mean_diff': diffs.mean(),
            'ci_lower': lower, 'ci_upper': upper,
            'contains_zero': lower <= 0 <= upper,
            'distribution': diffs
        }

    # ------------------------------------------------------------------
    # 4. Peeking-problem simulation
    # ------------------------------------------------------------------
    def simulate_peeking_risk(self, true_rate_a: float, true_rate_b: float,
                               n_per_group: int, checks_per_experiment: int,
                               n_simulations: int = 2000) -> dict:
        """
        Simulates repeatedly checking an experiment's significance at several
        points before it reaches full sample size, stopping the moment p < alpha
        is seen ("peeking"). Compares the resulting false-positive rate against
        checking only once at the final sample size — when true_rate_a == true_rate_b,
        any "significant" result found by peeking is a false positive by definition.

        Returns the inflated false-positive rate vs. the nominal alpha.
        """
        checkpoints = np.linspace(n_per_group / checks_per_experiment, n_per_group,
                                   checks_per_experiment).astype(int)
        peeked_false_positives = 0
        final_only_false_positives = 0

        for _ in range(n_simulations):
            sample_a = self.rng.binomial(1, true_rate_a, n_per_group)
            sample_b = self.rng.binomial(1, true_rate_b, n_per_group)

            stopped_early = False
            for n in checkpoints:
                count = np.array([sample_a[:n].sum(), sample_b[:n].sum()])
                nobs = np.array([n, n])
                if nobs.min() < 2 or count.max() == 0:
                    continue
                _, p_val = proportions_ztest(count, nobs)
                if p_val < self.alpha:
                    peeked_false_positives += 1
                    stopped_early = True
                    break

            count_final = np.array([sample_a.sum(), sample_b.sum()])
            _, p_final = proportions_ztest(count_final, np.array([n_per_group, n_per_group]))
            if p_final < self.alpha:
                final_only_false_positives += 1

        return {
            'nominal_alpha': self.alpha,
            'peeking_false_positive_rate': peeked_false_positives / n_simulations,
            'final_only_false_positive_rate': final_only_false_positives / n_simulations,
            'inflation_factor': (peeked_false_positives / n_simulations) / self.alpha
        }


if __name__ == '__main__':
    # Quick self-test against the Cookie Cats dataset
    df = pd.read_csv('C:\\Users\\klsat\\OneDrive\\Documents\\PW Skills\\PW Skills\\Statistics\\projects\\AB_Testing Framework\\cookie_cats.csv')
    fw = ABTestFramework(alpha=0.05, power=0.8)

    baseline = df[df['version'] == 'gate_30']['retention_7'].mean()
    print(f"Baseline (gate_30) 7-day retention: {baseline:.4f}")
    print(f"Required sample size per group for a 1pp MDE: {fw.calculate_sample_size(baseline, 0.01):,}")
    print(f"MDE achievable with actual sample size: {fw.minimum_detectable_effect(baseline, 44700):.4f}")

    result = fw.run_test(df[df['version'] == 'gate_30']['retention_7'],
                          df[df['version'] == 'gate_40']['retention_7'])
    print(f"\n7-day retention test result: {result}")
