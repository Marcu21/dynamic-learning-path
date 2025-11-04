import React, { useState, useEffect, type FC, useRef } from "react"
import { motion, useInView, useMotionValue, useTransform, animate } from "framer-motion"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend } from "recharts"
import { BookOpen, TrendingUp, BarChart as BarChartIcon, Sparkles, Trophy, Users, Award } from "lucide-react"
import type { StatisticsChartsProps } from "@/types/user-statistics"


export async function getServerSideProps() {
  return {
    props: {},
  };
}

// Time Period Selector Component
const TimePeriodSelector: FC<{ selected: number; onSelect: (days: number) => void }> = ({ selected, onSelect }) => {
  const periods = [7, 30, 90];
  return (
    <div className="flex justify-center p-1 rounded-lg backdrop-blur-sm shadow-inner bg-gray-500/5">
      {periods.map((period) => (
        <motion.button
          key={period}
          onClick={() => onSelect(period)}
          className={`relative px-4 py-2 text-sm font-semibold rounded-md transition-colors ${
            selected === period ? "text-white" : "text-gray-600 hover:text-gray-900"
          }`}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {selected === period && (
            <motion.div
              layoutId="timePeriod"
              className="absolute inset-0 bg-gradient-to-r from-purple-500 to-purple-600 rounded-md shadow-md"
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            />
          )}
          <span className="relative z-10">{period} days</span>
        </motion.button>
      ))}
    </div>
  );
};

// Generate daily data from the time period
const generateDailyData = (learningTimeData: Record<string, number> | undefined, timePeriod: number) => {
  if (!learningTimeData) return [];

  const today = new Date();
  const result = [];

  for (let i = timePeriod - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];

    result.push({
      date: dateStr,
      minutes: learningTimeData[dateStr] || 0
    });
  }

  return result;
};

// Generate platform data
const generatePlatformData = (platformTimeSummary: Record<string, number> | undefined) => {
  if (!platformTimeSummary) return [];

  const colors = ['#8B5CF6', '#06B6D4', '#10B981', '#F59E0B', '#EF4444', '#EC4899'];
  let colorIndex = 0;

  return Object.entries(platformTimeSummary)
    .filter(([_, percentage]) => percentage > 0)
    .map(([platform, percentage]) => ({
      name: platform,
      value: percentage,
      fill: colors[colorIndex++ % colors.length]
    }));
};

// Custom Tooltip Components
const CustomLineTooltip: FC<any> = ({ active, payload, label }) => {
  if (active && payload?.length) {
    const date = new Date(label);
    const formattedDate = date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      weekday: "short"
    });

    return (
      <div className="bg-white/95 backdrop-blur-sm rounded-lg p-3 shadow-lg border border-gray-200/50">
        <p className="font-semibold text-gray-800">{formattedDate}</p>
        <p style={{ color: '#8B5CF6' }} className="text-sm">
          Learned: {Math.round(Number(payload[0].value))} minutes
        </p>
      </div>
    );
  }
  return null;
};

const CustomPieTooltip: FC<any> = ({ active, payload }) => {
  if (active && payload?.length) {
    const data = payload[0];
    return (
      <div className="bg-white/95 backdrop-blur-sm rounded-lg p-3 shadow-lg border border-gray-200/50">
        <p className="font-semibold text-neutral-dark">{data.name}</p>
        <p style={{ color: data.payload.fill }} className="text-sm">
          {data.value.toFixed(1)}% of time
        </p>
      </div>
    );
  }
  return null;
};

const CustomBarTooltip: FC<any> = ({ active, payload, label }) => {
  if (active && payload?.length) {
    const data = payload[0];
    return (
      <div className="bg-white/95 backdrop-blur-sm rounded-lg p-3 shadow-lg border border-gray-200/50">
        <p className="font-semibold text-gray-800">{label}</p>
        <p style={{ color: data.payload.fill }} className="text-sm">
          {data.value.toFixed(0)} minutes
        </p>
      </div>
    );
  }
  return null;
};

// Animated Counter Component
const AnimatedCounter: FC<{ to: number; toFixedValue?: number; suffix?: string }> = ({
  to,
  toFixedValue = 0,
  suffix = ""
}) => {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });
  const count = useMotionValue(0);
  const rounded = useTransform(count, latest => `${latest.toFixed(toFixedValue)}${suffix}`);

  useEffect(() => {
    if (isInView) {
      const controls = animate(count, to, { duration: 1.5, ease: "easeOut" });
      return controls.stop;
    }
  }, [isInView, count, to, toFixedValue]);

  return <motion.span ref={ref}>{rounded}</motion.span>;
};

// Main Component
const StatisticsCharts: React.FC<StatisticsChartsProps> = ({
  statistics,
  timePeriod: initialTimePeriod
}) => {
  const [isReadyForCharts, setIsReadyForCharts] = useState(false);
  const [timePeriod, setTimePeriod] = useState(initialTimePeriod);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsReadyForCharts(true);
    }, 350);

    return () => clearTimeout(timer);
  }, [timePeriod]);

  // Generate chart data
  const dailyProgressData = generateDailyData(statistics.learning_time_data, timePeriod);
  const platformDistributionData = generatePlatformData(statistics.platform_time_summary);
  const isSingle = platformDistributionData.length === 1;

  // Generate comparison data for "Where You Stand"
  const userVsAverageData = [
    {
      name: "You",
      minutes: statistics.user_total_minutes || 0,
      fill: "#3B82F6"
    },
    {
      name: "Community Avg",
      minutes: statistics.community_average_minutes || 0,
      fill: "#10B981"
    }
  ];

  const formatDateTick = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  if (!statistics || !statistics.learning_time_data) {
    return (
      <div className="flex items-center justify-center p-8">
        <div>Loading statistics...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Daily Learning Activity Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="relative bg-white/80 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-gray-100/50"
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-100/80">
              <TrendingUp className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h4 className="text-lg font-bold text-gray-800">Daily Learning Activity</h4>
              <p className="text-sm text-gray-600">Minutes spent learning each day</p>
            </div>
          </div>
          <TimePeriodSelector selected={timePeriod} onSelect={setTimePeriod} />
        </div>
        <div className="h-64">
          {isReadyForCharts && dailyProgressData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dailyProgressData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatDateTick}
                  tick={{ fontSize: 10, fill: "#6b7280" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis tick={{ fontSize: 12, fill: "#6b7280" }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomLineTooltip />} />
                <Line
                  type="monotone"
                  dataKey="minutes"
                  stroke="#8B5CF6"
                  strokeWidth={3}
                  dot={{ fill: "#8B5CF6", r: 4 }}
                  name="Learned"
                  isAnimationActive={true}
                  animationDuration={1500}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-full text-sm text-gray-500">
              No learning activity data available for the selected period.
            </div>
          )}
        </div>
      </motion.div>

      {/* Grid with Focus Areas and Where You Stand */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Your Focus Areas (Platform Distribution) */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="relative bg-white/80 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-gray-100/50"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-green-100/80">
              <BookOpen className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h4 className="text-lg font-bold text-gray-800">Your Focus Areas</h4>
              <p className="text-sm text-gray-600">Time distribution across platforms</p>
            </div>
          </div>
          <div className="h-48">
            {isReadyForCharts && platformDistributionData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={platformDistributionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={isSingle ? 0 : 3}
                    startAngle={90}
                    endAngle={450}
                    dataKey="value"
                    nameKey="name"
                    isAnimationActive={!isSingle}
                    stroke={isSingle ? "none" : undefined}
                  >
                    {platformDistributionData.map((entry) => (
                      <Cell
                        key={`cell-${entry.name}`}
                        fill={entry.fill}
                        stroke={isSingle ? "none" : entry.fill}
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomPieTooltip />} />
                  <Legend
                    iconSize={10}
                    wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }}
                    formatter={(value) => <span className="text-neutral-dark">{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-sm text-gray-500">
                No platform data available.
              </div>
            )}
          </div>
        </motion.div>

        {/* Where You Stand (User vs Community Average) */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white/80 backdrop-blur-sm rounded-xl p-6 shadow-lg border border-gray-100/50"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-blue-100/80">
              <BarChartIcon className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h4 className="text-lg font-bold text-gray-800">Where You Stand</h4>
              <p className="text-sm text-gray-600">Your study time vs community average</p>
            </div>
          </div>
          <div className="h-48">
            {isReadyForCharts && userVsAverageData.some(d => d.minutes > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={userVsAverageData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 12, fill: "#6b7280" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis tick={{ fontSize: 12, fill: "#6b7280" }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomBarTooltip />} cursor={{ fill: "rgba(243, 244, 246, 0.5)" }} />
                  <Bar dataKey="minutes" radius={[8, 8, 0, 0]} animationDuration={1500}>
                    {userVsAverageData.map((entry) => (
                      <Cell key={`cell-${entry.name}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-sm text-gray-500">
                No comparison data available.
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Key Insights Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white/80 backdrop-blur-xl rounded-xl p-6 shadow-lg border border-gray-100/30 hover:shadow-xl hover:bg-white/90 transition-all duration-500"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-gradient-to-r from-purple-100 to-pink-100">
            <Sparkles className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h4 className="text-lg font-bold text-gray-800">Key Insights</h4>
            <p className="text-sm text-gray-600">Your learning performance highlights</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Performance Percentile */}
          {statistics.top_percentile_time !== undefined && (
            <div className="text-center p-4 bg-gradient-to-br from-blue-50/50 to-indigo-50/50 rounded-lg border border-blue-100/50">
              <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg">
                <Trophy className="w-6 h-6 text-white" />
              </div>
              <p className="text-2xl font-bold text-blue-700 mb-1">
                <AnimatedCounter to={Math.max(0.1, statistics.top_percentile_time)} toFixedValue={1} suffix="%" />
              </p>
              <p className="text-sm text-neutral-dark font-bold">Top Percentile</p>
              <p className="text-xs text-neutral-dark mt-1">Based on learning time</p>
            </div>
          )}

          {/* Community Impact */}
          {statistics.community_impact !== undefined && (
            <div className="text-center p-4 bg-gradient-to-br from-green-50/50 to-emerald-50/50 rounded-lg border border-green-100/50">
              <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-gradient-to-r from-green-500 to-emerald-600 flex items-center justify-center shadow-lg">
                <Users className="w-6 h-6 text-white" />
              </div>
              <p className="text-2xl font-bold text-green-700 mb-1">
                <AnimatedCounter to={Math.min(100, statistics.community_impact * 100)} toFixedValue={1} suffix="%" />
              </p>
              <p className="text-sm text-neutral-dark font-bold">Community Impact</p>
              <p className="text-xs text-neutral-dark mt-1">Your contribution</p>
            </div>
          )}

          {/* Content Coverage */}
          {statistics.content_coverage !== undefined && (
            <div className="text-center p-4 bg-gradient-to-br from-orange-50/50 to-amber-50/50 rounded-lg border border-orange-100/50">
              <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-gradient-to-r from-orange-500 to-amber-600 flex items-center justify-center shadow-lg">
                <Award className="w-6 h-6 text-white" />
              </div>
              <p className="text-2xl font-bold text-orange-700 mb-1">
                <AnimatedCounter to={statistics.content_coverage} toFixedValue={1} suffix="%" />
              </p>
              <p className="text-sm text-neutral-dark font-bold">Content Coverage</p>
              <p className="text-xs text-neutral-dark mt-1">Of your learning paths</p>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default StatisticsCharts;