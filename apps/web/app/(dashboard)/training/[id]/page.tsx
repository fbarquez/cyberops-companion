"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  BookOpen,
  Clock,
  Target,
  Play,
  CheckCircle,
  Lock,
  FileText,
  Video,
  HelpCircle,
  ExternalLink,
  Award,
  ChevronRight,
  AlertCircle,
} from "lucide-react";
import { Header } from "@/components/shared/header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { PageLoading } from "@/components/shared/loading";
import { useAuthStore } from "@/stores/auth-store";
import { useTranslations } from "@/hooks/use-translations";
import { trainingAPI } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

// Type definitions
interface TrainingModule {
  id: string;
  title: string;
  description?: string;
  module_type: string;
  estimated_duration_minutes?: number;
  order_index: number;
  user_completed?: boolean;
  is_locked?: boolean;
}

interface TrainingCourse {
  id: string;
  title: string;
  description?: string;
  course_code?: string;
  difficulty?: string;
  category?: string;
  estimated_duration_minutes?: number;
  passing_score?: number;
  certificate_enabled?: boolean;
  objectives?: string[];
  compliance_frameworks?: string[];
  control_references?: string[];
}

interface ModulesData {
  items: TrainingModule[];
}

interface Enrollment {
  course_id: string;
  progress_percent: number;
  deadline?: string;
  is_overdue?: boolean;
}

interface MyLearning {
  in_progress: Enrollment[];
  assigned: Enrollment[];
  completed: Enrollment[];
}

const moduleTypeIcons: Record<string, React.ElementType> = {
  video: Video,
  text: FileText,
  interactive: Play,
  quiz: HelpCircle,
  document: FileText,
  external_link: ExternalLink,
};

const difficultyColors: Record<string, string> = {
  beginner: "bg-green-500/10 text-green-600 border-green-500/20",
  intermediate: "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
  advanced: "bg-red-500/10 text-red-600 border-red-500/20",
};

export default function CourseDetailPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const { id } = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();

  // Fetch course details
  const { data: course, isLoading: courseLoading } = useQuery({
    queryKey: ["training-course", id],
    queryFn: () => trainingAPI.getCourse(token!, id as string) as Promise<TrainingCourse>,
    enabled: !!token && !!id,
  });

  // Fetch modules
  const { data: modulesData, isLoading: modulesLoading } = useQuery({
    queryKey: ["course-modules", id],
    queryFn: () => trainingAPI.getCourseModules(token!, id as string) as Promise<ModulesData>,
    enabled: !!token && !!id,
  });

  // Get user enrollment status
  const { data: myLearning } = useQuery({
    queryKey: ["my-learning"],
    queryFn: () => trainingAPI.getMyLearning(token!) as Promise<MyLearning>,
    enabled: !!token,
  });

  // Enroll mutation
  const enrollMutation = useMutation({
    mutationFn: () => trainingAPI.enrollInCourse(token!, id as string),
    onSuccess: () => {
      toast.success(t("training.enrolledSuccessfully") || "Successfully enrolled in course!");
      queryClient.invalidateQueries({ queryKey: ["my-learning"] });
      queryClient.invalidateQueries({ queryKey: ["course-modules", id] });
    },
    onError: () => {
      toast.error(t("training.enrollmentFailed") || "Failed to enroll in course");
    },
  });

  if (courseLoading || modulesLoading) return <PageLoading />;

  if (!course) {
    return (
      <div className="flex flex-col h-full">
        <Header title={t("training.courseNotFound") || "Course Not Found"} />
        <div className="p-6">
          <Card>
            <CardContent className="py-12 text-center">
              <BookOpen className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-muted-foreground">{t("training.courseNotFoundMessage") || "The course you're looking for doesn't exist."}</p>
              <Button onClick={() => router.push("/training")} className="mt-4">
                <ArrowLeft className="h-4 w-4 mr-2" />
                {t("training.backToCatalog") || "Back to Catalog"}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const modules = modulesData?.items || [];
  const enrollment = myLearning?.in_progress?.find((e: any) => e.course_id === id) ||
                     myLearning?.assigned?.find((e: any) => e.course_id === id) ||
                     myLearning?.completed?.find((e: any) => e.course_id === id);

  const isEnrolled = !!enrollment;
  const completedModules = modules.filter((m: any) => m.user_completed).length;
  const progressPercent = enrollment?.progress_percent || (modules.length > 0 ? (completedModules / modules.length) * 100 : 0);

  // Find next module to complete
  const nextModule = modules.find((m: any) => !m.user_completed);

  return (
    <div className="flex flex-col h-full">
      <Header
        title={course?.title || "Course"}
        backHref="/training"
      />

      <div className="p-6 space-y-6 overflow-y-auto">
        {/* Course Header */}
        <div className="grid md:grid-cols-3 gap-6">
          <Card className="md:col-span-2">
            <CardHeader>
              <div className="flex items-start justify-between">
                <Badge variant="outline" className={difficultyColors[course.difficulty || "beginner"]}>
                  {t(`training.difficulty.${course.difficulty}`) || course.difficulty || "beginner"}
                </Badge>
                <Badge variant="outline">
                  {t(`training.categories.${course.category}`) || (course.category || "general").replace(/_/g, " ")}
                </Badge>
              </div>
              <CardTitle className="text-2xl mt-2">{course.title}</CardTitle>
              <CardDescription className="text-base">{course.description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Course Info */}
              <div className="flex flex-wrap gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  {course.estimated_duration_minutes} {t("training.minutes") || "minutes"}
                </div>
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-muted-foreground" />
                  {modules.length} {t("training.modules") || "modules"}
                </div>
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4 text-muted-foreground" />
                  {course.passing_score}% {t("training.passingScore") || "to pass"}
                </div>
                {course.certificate_enabled && (
                  <div className="flex items-center gap-2">
                    <Award className="h-4 w-4 text-muted-foreground" />
                    {t("training.certificateIncluded") || "Certificate included"}
                  </div>
                )}
              </div>

              {/* Learning Objectives */}
              {course.objectives && course.objectives.length > 0 && (
                <>
                  <Separator />
                  <div>
                    <h4 className="font-medium mb-2">{t("training.learningObjectives") || "Learning Objectives"}</h4>
                    <ul className="space-y-1">
                      {course.objectives.map((obj: string, i: number) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                          <CheckCircle className="h-4 w-4 mt-0.5 text-green-500 flex-shrink-0" />
                          {obj}
                        </li>
                      ))}
                    </ul>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Enrollment Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                {isEnrolled
                  ? t("training.yourProgress") || "Your Progress"
                  : t("training.enrollNow") || "Enroll Now"
                }
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {isEnrolled ? (
                <>
                  <div className="text-center">
                    <div className="text-4xl font-bold text-primary">{Math.round(progressPercent)}%</div>
                    <p className="text-sm text-muted-foreground">
                      {completedModules}/{modules.length} {t("training.modulesCompleted") || "modules completed"}
                    </p>
                  </div>
                  <Progress value={progressPercent} className="h-3" />

                  {enrollment?.deadline && (
                    <div className={cn(
                      "flex items-center gap-2 text-sm p-2 rounded-lg",
                      enrollment.is_overdue
                        ? "bg-destructive/10 text-destructive"
                        : "bg-muted"
                    )}>
                      {enrollment.is_overdue ? (
                        <AlertCircle className="h-4 w-4" />
                      ) : (
                        <Clock className="h-4 w-4" />
                      )}
                      {enrollment.is_overdue
                        ? t("training.overdueDeadline") || "Deadline passed"
                        : `${t("training.deadline") || "Deadline"}: ${new Date(enrollment.deadline).toLocaleDateString()}`
                      }
                    </div>
                  )}

                  {nextModule ? (
                    <Link href={`/training/${id}/module/${nextModule.id}`}>
                      <Button className="w-full">
                        <Play className="h-4 w-4 mr-2" />
                        {t("training.continueToNext") || "Continue to Next Module"}
                      </Button>
                    </Link>
                  ) : (
                    <div className="text-center p-4 bg-green-500/10 rounded-lg">
                      <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-500" />
                      <p className="font-medium text-green-600">
                        {t("training.courseCompleted") || "Course Completed!"}
                      </p>
                    </div>
                  )}
                </>
              ) : (
                <>
                  <p className="text-sm text-muted-foreground">
                    {t("training.enrollDescription") || "Enroll to start learning and track your progress."}
                  </p>
                  <Button
                    className="w-full"
                    onClick={() => enrollMutation.mutate()}
                    disabled={enrollMutation.isPending}
                  >
                    <Play className="h-4 w-4 mr-2" />
                    {enrollMutation.isPending
                      ? t("training.enrolling") || "Enrolling..."
                      : t("training.startLearning") || "Start Learning"
                    }
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Course Modules */}
        <Card>
          <CardHeader>
            <CardTitle>{t("training.courseContent") || "Course Content"}</CardTitle>
            <CardDescription>
              {modules.length} {t("training.modulesTotal") || "modules"} · {course.estimated_duration_minutes} {t("training.minutesTotal") || "minutes total"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {modules.map((module: any, index: number) => {
                const ModuleIcon = moduleTypeIcons[module.module_type] || FileText;
                const isCompleted = module.user_completed;
                const isLocked = !isEnrolled && index > 0;
                const isCurrent = isEnrolled && !isCompleted && index === completedModules;

                return (
                  <div
                    key={module.id}
                    className={cn(
                      "flex items-center gap-4 p-4 rounded-lg border transition-colors",
                      isCompleted && "bg-green-500/5 border-green-500/20",
                      isCurrent && "bg-primary/5 border-primary/20",
                      isLocked && "opacity-50"
                    )}
                  >
                    <div className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center",
                      isCompleted ? "bg-green-500 text-white" :
                      isCurrent ? "bg-primary text-white" :
                      "bg-muted text-muted-foreground"
                    )}>
                      {isCompleted ? (
                        <CheckCircle className="h-4 w-4" />
                      ) : isLocked ? (
                        <Lock className="h-4 w-4" />
                      ) : (
                        <span className="text-sm font-medium">{index + 1}</span>
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium">{module.title}</h4>
                        <Badge variant="outline" className="text-xs">
                          <ModuleIcon className="h-3 w-3 mr-1" />
                          {t(`training.moduleTypes.${module.module_type}`) || module.module_type}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground line-clamp-1">
                        {module.description}
                      </p>
                    </div>

                    <div className="flex items-center gap-4">
                      <span className="text-sm text-muted-foreground">
                        {module.estimated_duration_minutes} min
                      </span>
                      {isEnrolled && !isLocked && (
                        <Link href={`/training/${id}/module/${module.id}`}>
                          <Button size="sm" variant={isCurrent ? "default" : "ghost"}>
                            {isCompleted ? (
                              <>
                                {t("training.review") || "Review"}
                                <ChevronRight className="h-4 w-4 ml-1" />
                              </>
                            ) : (
                              <>
                                {isCurrent ? t("training.start") || "Start" : t("training.view") || "View"}
                                <ChevronRight className="h-4 w-4 ml-1" />
                              </>
                            )}
                          </Button>
                        </Link>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Compliance Mapping */}
        {((course.compliance_frameworks?.length ?? 0) > 0 || (course.control_references?.length ?? 0) > 0) && (
          <Card>
            <CardHeader>
              <CardTitle>{t("training.complianceMapping") || "Compliance Mapping"}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {course.compliance_frameworks?.map((framework: string) => (
                  <Badge key={framework} variant="secondary">
                    {framework.toUpperCase()}
                  </Badge>
                ))}
                {course.control_references?.map((control: string) => (
                  <Badge key={control} variant="outline">
                    {control}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
