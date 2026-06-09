import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Trophy, Users, TreePine, Zap } from 'lucide-react';

/**
 * Interface representing a user record listed on the leaderboard.
 */
interface LeaderboardUser {
  rank: number;
  name: string;
  saved: string;
  level: string;
  isUser?: boolean;
}

export default function CommunityPage() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Community Impact Engine</h1>
          <p className="text-muted-foreground mt-1 text-lg">Together, we are making a measurable difference.</p>
        </div>
        <div className="bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 px-4 py-2 rounded-lg font-medium flex items-center gap-2">
          <Users className="w-5 h-5" />
          14,205 Active Users
        </div>
      </header>

      {/* Global Impact Conversion */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="border-green-500/20 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <TreePine className="w-4 h-4 text-green-500" /> Trees Saved
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">12,840</div>
            <p className="text-xs text-muted-foreground mt-2">Equivalent to planting a small forest this month.</p>
          </CardContent>
        </Card>

        <Card className="border-blue-500/20 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <Zap className="w-4 h-4 text-blue-500" /> Energy Conserved
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">45.2 <span className="text-xl font-normal text-muted-foreground">MWh</span></div>
            <p className="text-xs text-muted-foreground mt-2">Enough to power 40 homes for a month.</p>
          </CardContent>
        </Card>

        <Card className="border-yellow-500/20 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <Trophy className="w-4 h-4 text-yellow-500" /> Coal Avoided
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">8.5 <span className="text-xl font-normal text-muted-foreground">Tons</span></div>
            <p className="text-xs text-muted-foreground mt-2">Kept safely in the ground.</p>
          </CardContent>
        </Card>
      </div>

      {/* Leaderboard */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>Global Leaderboard</CardTitle>
          <CardDescription>Top contributors to carbon reduction this week</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {([
              { rank: 1, name: "Sarah J.", saved: "145 kg CO₂", level: "Eco Master" },
              { rank: 2, name: "You", saved: "124 kg CO₂", level: "Seedling", isUser: true },
              { rank: 3, name: "Marcus T.", saved: "98 kg CO₂", level: "Sprout" },
            ] as LeaderboardUser[]).map((user) => (
              <div key={user.rank} className={`flex items-center justify-between p-4 rounded-lg border ${user.isUser ? 'border-green-500 bg-green-50 dark:bg-green-900/10' : 'bg-card'}`}>
                <div className="flex items-center gap-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${user.rank === 1 ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 dark:bg-gray-800'}`}>
                    {user.rank}
                  </div>
                  <div>
                    <p className="font-semibold">{user.name}</p>
                    <Badge variant="secondary" className="mt-1 text-xs">{user.level}</Badge>
                  </div>
                </div>
                <div className="font-bold text-green-600 dark:text-green-500">
                  -{user.saved}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

    </div>
  );
}
