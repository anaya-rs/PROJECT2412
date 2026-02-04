import { Panel } from '@/components/Panel';
import { ControlButton } from '@/components/ControlButton';
import { TextInput } from '@/components/TextInput';
import {
  User,
  Bell,
  Shield,
  Palette,
  Volume2,
  Globe,
  HelpCircle,
  LogOut,
  Save,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export default function Settings() {
  const { user, logout } = useAuth();

  return (
      <div className="p-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-heading font-bold text-4xl tracking-tight text-black mb-2">
            Settings
          </h1>
          <p className="text-lg text-muted">
            Manage your account and preferences
          </p>
        </div>

        {/* Accent bar */}
        <div className="h-1 w-24 bg-accent-yellow accent-bar-reveal mb-8"></div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Settings Navigation */}
          <div className="lg:col-span-1">
            <Panel>
              <nav className="space-y-2">
                {[
                  { icon: User, label: 'Profile', active: true },
                  { icon: Bell, label: 'Notifications', active: false },
                  { icon: Shield, label: 'Privacy', active: false },
                  { icon: Palette, label: 'Appearance', active: false },
                  { icon: Volume2, label: 'Audio', active: false },
                  { icon: Globe, label: 'Language', active: false },
                  { icon: HelpCircle, label: 'Help', active: false },
                ].map(({ icon: Icon, label, active }, index) => (
                  <div
                    key={index}
                    className={`px-4 py-3 text-sm font-medium transition-all duration-150 cursor-pointer ${
                      active
                        ? "bg-accent-yellow text-black border-l-4 border-black"
                        : "bg-white text-black hover:bg-accent-yellow border-l-4 border-transparent"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="w-4 h-4" />
                      <span>{label}</span>
                    </div>
                  </div>
                ))}
              </nav>
            </Panel>
          </div>

          {/* Settings Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Profile Settings */}
            <Panel>
              <h2 className="font-heading font-bold text-xl tracking-tight text-black mb-6">
                Profile Settings
              </h2>
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-black mb-2">
                    Username
                  </label>
                  <TextInput
                    value={user?.username || ''}
                    readOnly
                    className="bg-muted"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-black mb-2">
                    Email
                  </label>
                  <TextInput
                    value={user?.email || ''}
                    readOnly
                    className="bg-muted"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-black mb-2">
                    Bio
                  </label>
                  <textarea
                    className="w-full border-2 border-black px-3 py-2 text-sm rounded-md focus:outline-none focus:border-accent-orange bg-white"
                    rows={4}
                    placeholder="Tell us about yourself..."
                  />
                </div>

                <ControlButton 
                  variant="primary"
                  className="transform active:scale-95 transition-transform"
                >
                  <Save className="w-4 h-4 mr-2" />
                  Save Changes
                </ControlButton>
              </div>
            </Panel>

            {/* Learning Preferences */}
            <Panel>
              <h2 className="font-heading font-bold text-xl tracking-tight text-black mb-6">
                Learning Preferences
              </h2>
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-black mb-2">
                    Daily Goal (minutes)
                  </label>
                  <select className="w-full border-2 border-black px-3 py-2 text-sm rounded-md focus:outline-none focus:border-accent-orange bg-white">
                    <option>15 minutes</option>
                    <option>30 minutes</option>
                    <option>45 minutes</option>
                    <option>60 minutes</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-black mb-2">
                    Preferred Difficulty
                  </label>
                  <select className="w-full border-2 border-black px-3 py-2 text-sm rounded-md focus:outline-none focus:border-accent-orange bg-white">
                    <option>Beginner</option>
                    <option>Intermediate</option>
                    <option>Advanced</option>
                    <option>Mixed</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-black mb-2">
                    Learning Style
                  </label>
                  <div className="space-y-2">
                    {['Visual', 'Auditory', 'Kinesthetic', 'Reading'].map((style) => (
                      <label key={style} className="flex items-center gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          className="w-4 h-4 border-2 border-black rounded focus:outline-none focus:border-accent-orange"
                        />
                        <span className="text-sm">{style}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </Panel>

            {/* Notifications */}
            <Panel>
              <h2 className="font-heading font-bold text-xl tracking-tight text-black mb-6">
                Notifications
              </h2>
              <div className="space-y-4">
                {[
                  'Daily learning reminders',
                  'Achievement unlocked',
                  'Streak milestones',
                  'New lessons available',
                  'Weekly progress reports',
                ].map((notification, index) => (
                  <label key={index} className="flex items-center justify-between cursor-pointer">
                    <span className="text-sm">{notification}</span>
                    <input
                      type="checkbox"
                      defaultChecked={index < 3}
                      className="w-4 h-4 border-2 border-black rounded focus:outline-none focus:border-accent-orange"
                    />
                  </label>
                ))}
              </div>
            </Panel>

            {/* Danger Zone */}
            <Panel className="border-accent-orange">
              <h2 className="font-heading font-bold text-xl tracking-tight text-black mb-6">
                Danger Zone
              </h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">Sign Out</div>
                    <div className="text-sm text-muted">Sign out of your account</div>
                  </div>
                  <ControlButton 
                    variant="secondary"
                    onClick={logout}
                    className="transform active:scale-95 transition-transform"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Sign Out
                  </ControlButton>
                </div>
              </div>
            </Panel>
          </div>
        </div>
      </div>
  );
}
