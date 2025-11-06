import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  Svg: React.ComponentType<React.ComponentProps<'svg'>>;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: '成绩导入',
    Svg: require('@site/static/img/undraw_docusaurus_mountain.svg').default,
    description: (
      <>
        查分器提供了一系列方法已导入成绩并提供数据源，便于玩家将成绩上传至查分器进行分析和可视化。
      </>
    ),
  },
  {
    title: '数据统计与分析',
    Svg: require('@site/static/img/undraw_docusaurus_tree.svg').default,
    description: (
      <>
        查分器提供详尽的数据统计与分析，帮助玩家了解不同谱面下的自身表现和大数据，发现提升空间。
      </>
    ),
  },
  {
    title: '开发者接入友好',
    Svg: require('@site/static/img/undraw_docusaurus_react.svg').default,
    description: (
      <>
        查分器提供完善的 API 文档和示例代码，方便开发者快速集成和使用查分器功能，以接入第三方应用或 IM 机器人。
      </>
    ),
  },
];

function Feature({title, Svg, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
