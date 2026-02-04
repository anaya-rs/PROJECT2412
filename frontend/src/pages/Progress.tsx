import { Panel } from '@/components/Panel';
import { ControlButton } from '@/components/ControlButton';
import {
  Trophy,
  Target,
  TrendingUp,
  Star,
  Calendar,
  Clock,
  Award,
  Flame,
  Zap,
  BookOpen,
  CheckCircle,
} from 'lucide-react';

export default function Progress() {
  return (
      <div className="p-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-heading font-bold text-4xl tracking-tight text-black mb-2">
            Your Progress
          </h1>
          <p className="text-lg text-muted">
            Track your learning journey and achievements
          </p>
        </div>

        {/* Accent bar */}
        <div className="h-1 w-24 bg-accent-yellow accent-bar-reveal mb-8"></div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <Panel className="text-center hover:border-accent-amber transition-all duration-base ease-standard btn-active">
            <Trophy className="w-12 h-12 text-accent-yellow mx-auto mb-3" />
            <div className="text-3xl font-bold font-heading text-black mb-1">24</div>
            <div className="text-sm text-muted">Achievements</div>
          </Panel>
          
          <Panel className="text-center hover:border-accent-amber transition-all duration-base ease-standard btn-active">
            <Target className="w-12 h-12 text-accent-orange mx-auto mb-3" />
            <div className="text-3xl font-bold font-heading text-black mb-1">89%</div>
            <div className="text-sm text-muted">Completion Rate</div>
          </Panel>
          
          <Panel className="text-center hover:border-accent-amber transition-all duration-base ease-standard btn-active">
            <Flame className="w-12 h-12 text-accent-orange mx-auto mb-3" />
            <div className="text-3xl font-bold font-heading text-black mb-1">15</div>
            <div className="text-sm text-muted">Day Streak</div>
          </Panel>
          
          <Panel className="text-center hover:border-accent-amber transition-all duration-base ease-standard btn-active">
            <Star className="w-12 h-12 text-accent-yellow mx-auto mb-3" />
            <div className="text-3xl font-bold font-heading text-black mb-1">1,250</div>
            <div className="text-sm text-muted">Total Points</div>
          </Panel>
        </div>

        {/* Progress Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          <Panel>
            <h2 className="font-heading font-bold text-xl tracking-tight text-black mb-6">
              Weekly Activity
            </h2>
            <div className="space-y-4">
              {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, index) => (
                <div key={day} className="flex items-center gap-4">
                  <div className="w-12 text-sm font-medium">{day}</div>
                  <div className="flex-1 bg-black rounded-full h-4">
                    <div 
                      className="bg-accent-yellow h-4 rounded-full transition-all duration-300"
                      style={{width: `${Math.random() * 80 + 20}%`}}
                    ></div>
                  </div>
                  <div className="text-sm text-muted w-12 text-right">
                    {Math.floor(Math.random() * 5 + 1)}h
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel>
            <h2 className="font-heading font-bold text-xl tracking-tight text-black mb-6">
              Skill Progress
            </h2>
            <div className="space-y-6">
              {[
                { skill: 'JavaScript', progress: 75, color: 'accent-yellow' },
                { skill: 'React', progress: 60, color: 'accent-amber' },
                { skill: 'Python', progress: 90, color: 'accent-orange' },
                { skill: 'Data Structures', progress: 45, color: 'accent-yellow' },
                { skill: 'Algorithms', progress: 30, color: 'accent-amber' },
              ].map(({ skill, progress, color }) => (
                <div key={skill}>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="font-medium">{skill}</span>
                    <span className="text-muted">{progress}%</span>
                  </div>
                  <div className="w-full bg-black rounded-full h-3">
                    <div 
                      className={`bg-${color} h-3 rounded-full transition-all duration-300`}
                      style={{width: `${progress}%`}}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        {/* Recent Achievements */}
        <Panel className="mb-8">
          <h2 className="font-heading font-bold text-xl tracking-tight text-black mb-6">
            Recent Achievements
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { icon: Trophy, title: 'Quick Learner', desc: 'Complete 5 lessons in one day', earned: true },
              { icon: Zap, title: 'Speed Demon', desc: 'Finish a lesson in under 10 minutes', earned: true },
              { icon: Award, title: 'Perfect Score', desc: 'Get 100% on a quiz', earned: false },
              { icon: Flame, title: 'On Fire', desc: '7-day learning streak', earned: true },
              { icon: Star, title: 'Rising Star', desc: 'Reach level 10', earned: false },
              { icon: Target, title: 'Sharpshooter', desc: 'Answer 50 questions correctly', earned: true },
            ].map(({ icon: Icon, title, desc, earned }, index) => (
              <div 
                key={index}
                className={`p-4 border-2 rounded-md transition-all duration-150 ${
                  earned 
                    ? 'border-accent-yellow bg-accent-yellow/10 transform hover:scale-105' 
                    : 'border-black bg-white opacity-50'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <Icon className={`w-6 h-6 ${earned ? 'text-accent-yellow' : 'text-muted'}`} />
                  <h3 className={`font-heading font-semibold ${earned ? 'text-black' : 'text-muted'}`}>
                    {title}
                  </h3>
                </div>
                <p className="text-sm text-muted">{desc}</p>
                {earned && (
                  <div className="mt-2 text-xs font-medium text-accent-orange">
                    ✓ Earned
                  </div>
                )}
              </div>
            ))}
          </div>
        </Panel>

        {/* Learning Goals */}
        <Panel>
          <h2 className="font-heading font-bold text-xl tracking-tight text-black mb-6">
            Learning Goals
          </h2>
          <div className="space-y-4">
            {[
              { goal: 'Complete React Course', deadline: 'This week', progress: 80 },
              { goal: 'Master JavaScript ES6+', deadline: 'Next week', progress: 65 },
              { goal: 'Build 3 Projects', deadline: 'This month', progress: 33 },
            ].map(({ goal, deadline, progress }, index) => (
              <div key={index} className="flex items-center gap-4 p-4 border-2 border-black rounded-md">
                <CheckCircle className={`w-5 h-5 ${progress === 100 ? 'text-accent-yellow' : 'text-muted'}`} />
                <div className="flex-1">
                  <div className="font-medium">{goal}</div>
                  <div className="text-sm text-muted">{deadline}</div>
                </div>
                <div className="text-sm font-medium">{progress}%</div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
  );
}
