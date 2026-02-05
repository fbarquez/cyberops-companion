"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  GraduationCap,
  BookOpen,
  Trophy,
  Clock,
  Target,
  Play,
  CheckCircle,
  AlertCircle,
  Search,
  Filter,
  ChevronRight,
  Award,
  Zap,
  Shield,
  Lock,
  Mail,
  Globe,
  Smartphone,
  Cloud,
  Eye,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { trainingAPI } from "@/lib/api-client";
import { cn } from "@/lib/utils";

const categoryIcons: Record<string, React.ElementType> = {
  security_fundamentals: Shield,
  phishing_awareness: Mail,
  data_protection: Lock,
  password_security: Lock,
  social_engineering: Eye,
  compliance: BookOpen,
  incident_response: AlertCircle,
  physical_security: Shield,
  mobile_security: Smartphone,
  cloud_security: Cloud,
  privacy: Eye,
  custom: BookOpen,
};

const difficultyColors: Record<string, string> = {
  beginner: "bg-green-500/10 text-green-600 border-green-500/20",
  intermediate: "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
  advanced: "bg-red-500/10 text-red-600 border-red-500/20",
};

export default function TrainingPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const [activeTab, setActiveTab] = useState("catalog");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch course catalog
  const { data: catalog, isLoading: catalogLoading } = useQuery({
    queryKey: ["training-catalog", categoryFilter],
    queryFn: () =>
      trainingAPI.getCatalog(
        token!,
        1,
        50,
        categoryFilter !== "all" ? categoryFilter : undefined
      ),
    enabled: !!token,
  });

  // Fetch my learning
  const { data: myLearning, isLoading: learningLoading } = useQuery({
    queryKey: ["my-learning"],
    queryFn: () => trainingAPI.getMyLearning(token!),
    enabled: !!token,
  });

  // Fetch leaderboard
  const { data: leaderboard, isLoading: leaderboardLoading } = useQuery({
    queryKey: ["training-leaderboard"],
    queryFn: () => trainingAPI.getLeaderboard(token!, "all_time", 10),
    enabled: !!token,
  });

  // Fetch my stats
  const { data: myStats } = useQuery({
    queryKey: ["my-training-stats"],
    queryFn: () => trainingAPI.getMyStats(token!),
    enabled: !!token,
  });

  if (catalogLoading || learningLoading) return <PageLoading />;

  const courses = catalog?.items || [];
  const categories = catalog?.categories || [];

  const filteredCourses = courses.filter((course: any) =>
    course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    course.short_description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full">
      <Header title={t("training.title") || "Security Awareness Training"} />

      <div className="p-6 space-y-6 overflow-y-auto">
        {/* Stats Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <BookOpen className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{myStats?.courses_completed || 0}</p>
                  <p className="text-sm text-muted-foreground">{t("training.coursesCompleted") || "Courses Completed"}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-500/10 rounded-lg">
                  <Target className="h-5 w-5 text-yellow-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{myStats?.quizzes_passed || 0}</p>
                  <p className="text-sm text-muted-foreground">{t("training.quizzesPassed") || "Quizzes Passed"}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-500/10 rounded-lg">
                  <Trophy className="h-5 w-5 text-green-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{myStats?.total_points || 0}</p>
                  <p className="text-sm text-muted-foreground">{t("training.totalPoints") || "Total Points"}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-500/10 rounded-lg">
                  <Award className="h-5 w-5 text-purple-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{myStats?.badges_earned || 0}</p>
                  <p className="text-sm text-muted-foreground">{t("training.badgesEarned") || "Badges Earned"}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="catalog" className="flex items-center gap-2">
              <GraduationCap className="h-4 w-4" />
              {t("training.catalog") || "Course Catalog"}
            </TabsTrigger>
            <TabsTrigger value="my-learning" className="flex items-center gap-2">
              <BookOpen className="h-4 w-4" />
              {t("training.myLearning") || "My Learning"}
              {myLearning?.in_progress?.length > 0 && (
                <Badge variant="secondary" className="ml-1">
                  {myLearning.in_progress.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="leaderboard" className="flex items-center gap-2">
              <Trophy className="h-4 w-4" />
              {t("training.leaderboard") || "Leaderboard"}
            </TabsTrigger>
          </TabsList>

          {/* Course Catalog Tab */}
          <TabsContent value="catalog" className="space-y-4">
            {/* Filters */}
            <div className="flex flex-col md:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={t("training.searchCourses") || "Search courses..."}
                  className="pl-9"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-full md:w-[200px]">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder={t("training.filterByCategory") || "Filter by category"} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t("training.allCategories") || "All Categories"}</SelectItem>
                  {categories.map((cat: any) => (
                    <SelectItem key={cat.category} value={cat.category}>
                      {t(`training.categories.${cat.category}`) || cat.category.replace(/_/g, " ")} ({cat.count})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Course Grid */}
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredCourses.map((course: any) => {
                const CategoryIcon = categoryIcons[course.category] || BookOpen;
                return (
                  <Card key={course.id} className="flex flex-col hover:shadow-lg transition-shadow">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="p-2 bg-primary/10 rounded-lg">
                          <CategoryIcon className="h-6 w-6 text-primary" />
                        </div>
                        <div className="flex gap-2">
                          <Badge variant="outline" className={difficultyColors[course.difficulty]}>
                            {t(`training.difficulty.${course.difficulty}`) || course.difficulty}
                          </Badge>
                          {course.is_featured && (
                            <Badge className="bg-yellow-500">
                              <Zap className="h-3 w-3 mr-1" />
                              {t("training.featured") || "Featured"}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <CardTitle className="mt-4 line-clamp-2">{course.title}</CardTitle>
                      <CardDescription className="line-clamp-2">
                        {course.short_description}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="flex-1">
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          {course.estimated_duration_minutes} min
                        </div>
                        <div className="flex items-center gap-1">
                          <BookOpen className="h-4 w-4" />
                          {course.modules_count} {t("training.modules") || "modules"}
                        </div>
                      </div>
                      {course.user_enrollment_status && (
                        <div className="mt-4">
                          <div className="flex items-center justify-between text-sm mb-1">
                            <span>{t("training.progress") || "Progress"}</span>
                            <span>{Math.round(course.user_progress_percent || 0)}%</span>
                          </div>
                          <Progress value={course.user_progress_percent || 0} className="h-2" />
                        </div>
                      )}
                    </CardContent>
                    <CardFooter>
                      <Link href={`/training/${course.id}`} className="w-full">
                        <Button className="w-full" variant={course.user_enrollment_status ? "secondary" : "default"}>
                          {course.user_enrollment_status === "completed" ? (
                            <>
                              <CheckCircle className="h-4 w-4 mr-2" />
                              {t("training.reviewCourse") || "Review Course"}
                            </>
                          ) : course.user_enrollment_status ? (
                            <>
                              <Play className="h-4 w-4 mr-2" />
                              {t("training.continueLearning") || "Continue Learning"}
                            </>
                          ) : (
                            <>
                              <Play className="h-4 w-4 mr-2" />
                              {t("training.startCourse") || "Start Course"}
                            </>
                          )}
                        </Button>
                      </Link>
                    </CardFooter>
                  </Card>
                );
              })}
            </div>

            {filteredCourses.length === 0 && (
              <Card>
                <CardContent className="py-12 text-center">
                  <GraduationCap className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">
                    {t("training.noCourses") || "No courses found"}
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* My Learning Tab */}
          <TabsContent value="my-learning" className="space-y-6">
            {/* In Progress */}
            {myLearning?.in_progress?.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Play className="h-5 w-5 text-primary" />
                  {t("training.inProgress") || "In Progress"}
                </h3>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {myLearning.in_progress.map((item: any) => (
                    <LearningCard key={item.enrollment_id} item={item} />
                  ))}
                </div>
              </div>
            )}

            {/* Assigned */}
            {myLearning?.assigned?.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Target className="h-5 w-5 text-yellow-500" />
                  {t("training.assigned") || "Assigned to You"}
                  {myLearning.overdue > 0 && (
                    <Badge variant="destructive">{myLearning.overdue} {t("training.overdue") || "overdue"}</Badge>
                  )}
                </h3>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {myLearning.assigned.map((item: any) => (
                    <LearningCard key={item.enrollment_id} item={item} />
                  ))}
                </div>
              </div>
            )}

            {/* Completed */}
            {myLearning?.completed?.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  {t("training.completed") || "Completed"}
                </h3>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {myLearning.completed.map((item: any) => (
                    <LearningCard key={item.enrollment_id} item={item} />
                  ))}
                </div>
              </div>
            )}

            {(!myLearning?.in_progress?.length && !myLearning?.assigned?.length && !myLearning?.completed?.length) && (
              <Card>
                <CardContent className="py-12 text-center">
                  <BookOpen className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground mb-4">
                    {t("training.noEnrollments") || "You haven't enrolled in any courses yet"}
                  </p>
                  <Button onClick={() => setActiveTab("catalog")}>
                    {t("training.browseCatalog") || "Browse Course Catalog"}
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Leaderboard Tab */}
          <TabsContent value="leaderboard" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trophy className="h-5 w-5 text-yellow-500" />
                  {t("training.topPerformers") || "Top Performers"}
                </CardTitle>
                <CardDescription>
                  {t("training.leaderboardDescription") || "See how you rank against your colleagues"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {leaderboardLoading ? (
                  <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-16 bg-muted animate-pulse rounded-lg" />
                    ))}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {leaderboard?.entries?.map((entry: any, index: number) => (
                      <div
                        key={entry.user_id}
                        className={cn(
                          "flex items-center gap-4 p-4 rounded-lg",
                          index === 0 ? "bg-yellow-500/10 border border-yellow-500/20" :
                          index === 1 ? "bg-gray-500/10 border border-gray-500/20" :
                          index === 2 ? "bg-amber-700/10 border border-amber-700/20" :
                          "bg-muted/50"
                        )}
                      >
                        <div className={cn(
                          "w-8 h-8 rounded-full flex items-center justify-center font-bold",
                          index === 0 ? "bg-yellow-500 text-white" :
                          index === 1 ? "bg-gray-400 text-white" :
                          index === 2 ? "bg-amber-700 text-white" :
                          "bg-muted text-muted-foreground"
                        )}>
                          {entry.rank}
                        </div>
                        <div className="flex-1">
                          <p className="font-medium">{entry.user_name}</p>
                          <p className="text-sm text-muted-foreground">
                            {entry.courses_completed} {t("training.courses") || "courses"} · {entry.badges_earned} {t("training.badges") || "badges"}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-lg">{entry.total_points}</p>
                          <p className="text-sm text-muted-foreground">{t("training.points") || "points"}</p>
                        </div>
                        {entry.current_streak_days > 0 && (
                          <Badge variant="outline" className="ml-2">
                            <Zap className="h-3 w-3 mr-1" />
                            {entry.current_streak_days}d streak
                          </Badge>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {leaderboard?.current_user_rank && leaderboard.current_user_rank > 10 && (
                  <div className="mt-6 pt-4 border-t">
                    <div className="flex items-center gap-4 p-4 bg-primary/5 rounded-lg border border-primary/20">
                      <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-bold">
                        {leaderboard.current_user_rank}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">{t("training.yourRank") || "Your Rank"}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-lg">{leaderboard.current_user_points}</p>
                        <p className="text-sm text-muted-foreground">{t("training.points") || "points"}</p>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function LearningCard({ item }: { item: any }) {
  const { t } = useTranslations();
  const CategoryIcon = categoryIcons[item.course_category] || BookOpen;

  return (
    <Card className={cn(
      "hover:shadow-md transition-shadow",
      item.is_overdue && "border-destructive/50"
    )}>
      <CardContent className="pt-6">
        <div className="flex items-start gap-3 mb-4">
          <div className="p-2 bg-primary/10 rounded-lg">
            <CategoryIcon className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-medium truncate">{item.course_title}</h4>
            <p className="text-sm text-muted-foreground">{item.course_code}</p>
          </div>
          <Badge variant="outline" className={difficultyColors[item.course_difficulty]}>
            {item.course_difficulty}
          </Badge>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">{t("training.progress") || "Progress"}</span>
            <span>{item.modules_completed}/{item.total_modules} {t("training.modules") || "modules"}</span>
          </div>
          <Progress value={item.progress_percent} className="h-2" />
        </div>

        {item.deadline && (
          <div className={cn(
            "mt-3 flex items-center gap-2 text-sm",
            item.is_overdue ? "text-destructive" : "text-muted-foreground"
          )}>
            {item.is_overdue ? (
              <AlertCircle className="h-4 w-4" />
            ) : (
              <Clock className="h-4 w-4" />
            )}
            {item.is_overdue
              ? t("training.overdueBy") || "Overdue"
              : `${t("training.dueBy") || "Due by"} ${new Date(item.deadline).toLocaleDateString()}`
            }
          </div>
        )}

        <Link href={`/training/${item.course_id}`} className="block mt-4">
          <Button className="w-full" variant="secondary" size="sm">
            {item.status === "completed" ? (
              <>
                <CheckCircle className="h-4 w-4 mr-2" />
                {t("training.review") || "Review"}
              </>
            ) : (
              <>
                <ChevronRight className="h-4 w-4 mr-2" />
                {t("training.continue") || "Continue"}
              </>
            )}
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}
