"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Clock,
  CheckCircle,
  Play,
  Pause,
  FileText,
  Video,
  HelpCircle,
  ExternalLink,
  Download,
  RefreshCw,
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

const moduleTypeIcons: Record<string, React.ElementType> = {
  video: Video,
  text: FileText,
  interactive: Play,
  quiz: HelpCircle,
  document: FileText,
  external_link: ExternalLink,
};

export default function ModuleViewerPage() {
  const { t } = useTranslations();
  const { token } = useAuthStore();
  const { id: courseId, moduleId } = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [timeSpent, setTimeSpent] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);

  // Fetch module details
  const { data: module, isLoading: moduleLoading } = useQuery({
    queryKey: ["training-module", moduleId],
    queryFn: () => trainingAPI.getModule(token!, moduleId as string),
    enabled: !!token && !!moduleId,
  });

  // Fetch course details
  const { data: course } = useQuery({
    queryKey: ["training-course", courseId],
    queryFn: () => trainingAPI.getCourse(token!, courseId as string),
    enabled: !!token && !!courseId,
  });

  // Fetch all modules for navigation
  const { data: modulesData } = useQuery({
    queryKey: ["course-modules", courseId],
    queryFn: () => trainingAPI.getCourseModules(token!, courseId as string),
    enabled: !!token && !!courseId,
  });

  // Fetch module progress
  const { data: progress } = useQuery({
    queryKey: ["module-progress", moduleId],
    queryFn: () => trainingAPI.getModuleProgress(token!, moduleId as string),
    enabled: !!token && !!moduleId,
  });

  // Update progress mutation
  const updateProgressMutation = useMutation({
    mutationFn: (data: { progress_percent: number; time_spent_seconds: number }) =>
      trainingAPI.updateModuleProgress(token!, moduleId as string, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["module-progress", moduleId] });
    },
  });

  // Complete module mutation
  const completeModuleMutation = useMutation({
    mutationFn: () => trainingAPI.completeModule(token!, moduleId as string),
    onSuccess: () => {
      toast.success(t("training.moduleCompleted") || "Module completed!");
      queryClient.invalidateQueries({ queryKey: ["module-progress", moduleId] });
      queryClient.invalidateQueries({ queryKey: ["course-modules", courseId] });
      queryClient.invalidateQueries({ queryKey: ["my-learning"] });
    },
    onError: () => {
      toast.error(t("training.completionFailed") || "Failed to mark module as complete");
    },
  });

  // Track time spent
  useEffect(() => {
    if (!isPlaying || module?.user_completed) return;

    const interval = setInterval(() => {
      setTimeSpent((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [isPlaying, module?.user_completed]);

  // Auto-save progress every 30 seconds
  useEffect(() => {
    if (timeSpent > 0 && timeSpent % 30 === 0 && !module?.user_completed) {
      const estimatedProgress = Math.min(
        Math.round((timeSpent / (module?.estimated_duration_minutes || 10) / 60) * 100),
        99
      );
      updateProgressMutation.mutate({
        progress_percent: estimatedProgress,
        time_spent_seconds: timeSpent,
      });
    }
  }, [timeSpent, module?.estimated_duration_minutes, module?.user_completed]);

  if (moduleLoading) return <PageLoading />;

  if (!module) {
    return (
      <div className="flex flex-col h-full">
        <Header title={t("training.moduleNotFound") || "Module Not Found"} />
        <div className="p-6">
          <Card>
            <CardContent className="py-12 text-center">
              <BookOpen className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-muted-foreground">{t("training.moduleNotFoundMessage") || "The module you're looking for doesn't exist."}</p>
              <Button onClick={() => router.push(`/training/${courseId}`)} className="mt-4">
                <ArrowLeft className="h-4 w-4 mr-2" />
                {t("training.backToCourse") || "Back to Course"}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const modules = modulesData?.items || [];
  const currentIndex = modules.findIndex((m: any) => m.id === moduleId);
  const prevModule = currentIndex > 0 ? modules[currentIndex - 1] : null;
  const nextModule = currentIndex < modules.length - 1 ? modules[currentIndex + 1] : null;

  const ModuleIcon = moduleTypeIcons[module.module_type] || FileText;
  const isCompleted = module.user_completed;

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const handleComplete = () => {
    completeModuleMutation.mutate();
  };

  const renderContent = () => {
    switch (module.module_type) {
      case "video":
        return (
          <div className="space-y-4">
            {module.video_url ? (
              <div className="aspect-video bg-black rounded-lg overflow-hidden">
                <iframe
                  src={module.video_url}
                  className="w-full h-full"
                  allowFullScreen
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                />
              </div>
            ) : (
              <div className="aspect-video bg-muted rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <Video className="h-12 w-12 mx-auto mb-2 text-muted-foreground" />
                  <p className="text-muted-foreground">{t("training.noVideoAvailable") || "No video available"}</p>
                </div>
              </div>
            )}
            {module.content && (
              <div className="prose dark:prose-invert max-w-none">
                <div dangerouslySetInnerHTML={{ __html: module.content }} />
              </div>
            )}
          </div>
        );

      case "text":
      case "document":
        return (
          <div className="space-y-4">
            {module.content ? (
              <div className="prose dark:prose-invert max-w-none bg-card p-6 rounded-lg border">
                <div dangerouslySetInnerHTML={{ __html: module.content }} />
              </div>
            ) : module.attachment_id ? (
              <Card>
                <CardContent className="py-8 text-center">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="mb-4">{t("training.downloadDocument") || "Download the document to continue learning"}</p>
                  <Button>
                    <Download className="h-4 w-4 mr-2" />
                    {t("training.download") || "Download"}
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="py-8 text-center">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">{t("training.noContentAvailable") || "No content available"}</p>
                </CardContent>
              </Card>
            )}
          </div>
        );

      case "external_link":
        return (
          <Card>
            <CardContent className="py-8 text-center">
              <ExternalLink className="h-12 w-12 mx-auto mb-4 text-primary" />
              <p className="mb-4">{t("training.externalResource") || "This module links to an external resource"}</p>
              {module.external_url && (
                <Button asChild>
                  <a href={module.external_url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    {t("training.openResource") || "Open Resource"}
                  </a>
                </Button>
              )}
              {module.content && (
                <div className="mt-6 prose dark:prose-invert max-w-none text-left">
                  <div dangerouslySetInnerHTML={{ __html: module.content }} />
                </div>
              )}
            </CardContent>
          </Card>
        );

      case "quiz":
        return (
          <Card>
            <CardContent className="py-8 text-center">
              <HelpCircle className="h-12 w-12 mx-auto mb-4 text-primary" />
              <h3 className="text-lg font-semibold mb-2">{t("training.quizModule") || "Quiz Module"}</h3>
              <p className="text-muted-foreground mb-4">
                {t("training.quizDescription") || "Test your knowledge with this quiz"}
              </p>
              {module.quiz_id ? (
                <Button asChild>
                  <Link href={`/training/${courseId}/quiz/${module.quiz_id}`}>
                    <Play className="h-4 w-4 mr-2" />
                    {t("training.startQuiz") || "Start Quiz"}
                  </Link>
                </Button>
              ) : (
                <Button disabled>
                  <AlertCircle className="h-4 w-4 mr-2" />
                  {t("training.quizNotAvailable") || "Quiz not available"}
                </Button>
              )}
            </CardContent>
          </Card>
        );

      case "interactive":
        return (
          <div className="space-y-4">
            {module.content ? (
              <div className="prose dark:prose-invert max-w-none bg-card p-6 rounded-lg border">
                <div dangerouslySetInnerHTML={{ __html: module.content }} />
              </div>
            ) : (
              <Card>
                <CardContent className="py-8 text-center">
                  <Play className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">{t("training.interactiveNotAvailable") || "Interactive content not available"}</p>
                </CardContent>
              </Card>
            )}
          </div>
        );

      default:
        return (
          <Card>
            <CardContent className="py-8 text-center">
              <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-muted-foreground">{t("training.unknownModuleType") || "Unknown module type"}</p>
            </CardContent>
          </Card>
        );
    }
  };

  return (
    <div className="flex flex-col h-full">
      <Header
        title={module.title}
        breadcrumbs={[
          { label: t("training.title") || "Training", href: "/training" },
          { label: course?.title || "Course", href: `/training/${courseId}` },
          { label: `Module ${currentIndex + 1}` },
        ]}
      />

      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6 max-w-5xl mx-auto">
          {/* Module Header */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline">
                      <ModuleIcon className="h-3 w-3 mr-1" />
                      {t(`training.moduleTypes.${module.module_type}`) || module.module_type}
                    </Badge>
                    {isCompleted && (
                      <Badge className="bg-green-500">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        {t("training.completed") || "Completed"}
                      </Badge>
                    )}
                  </div>
                  <CardTitle className="text-xl">{module.title}</CardTitle>
                  {module.description && (
                    <CardDescription className="mt-1">{module.description}</CardDescription>
                  )}
                </div>
                <div className="flex flex-col items-end gap-2 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {module.estimated_duration_minutes} {t("training.minutes") || "min"}
                  </div>
                  {!isCompleted && (
                    <div className="flex items-center gap-1">
                      <RefreshCw className="h-4 w-4" />
                      {formatTime(timeSpent)}
                    </div>
                  )}
                </div>
              </div>

              {/* Progress bar */}
              {!isCompleted && progress && (
                <div className="mt-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span>{t("training.progress") || "Progress"}</span>
                    <span>{progress.progress_percent || 0}%</span>
                  </div>
                  <Progress value={progress.progress_percent || 0} className="h-2" />
                </div>
              )}
            </CardHeader>
          </Card>

          {/* Module Content */}
          {renderContent()}

          {/* Completion Section */}
          {!isCompleted && module.module_type !== "quiz" && (
            <Card>
              <CardContent className="py-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{t("training.readyToComplete") || "Ready to complete this module?"}</h4>
                    <p className="text-sm text-muted-foreground">
                      {t("training.markAsComplete") || "Mark this module as complete to track your progress"}
                    </p>
                  </div>
                  <Button
                    onClick={handleComplete}
                    disabled={completeModuleMutation.isPending}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    {completeModuleMutation.isPending ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        {t("training.completing") || "Completing..."}
                      </>
                    ) : (
                      <>
                        <CheckCircle className="h-4 w-4 mr-2" />
                        {t("training.markComplete") || "Mark as Complete"}
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Navigation */}
          <div className="flex items-center justify-between pt-4">
            {prevModule ? (
              <Link href={`/training/${courseId}/module/${prevModule.id}`}>
                <Button variant="outline">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  {t("training.previousModule") || "Previous"}
                </Button>
              </Link>
            ) : (
              <Link href={`/training/${courseId}`}>
                <Button variant="outline">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  {t("training.backToCourse") || "Back to Course"}
                </Button>
              </Link>
            )}

            {nextModule ? (
              <Link href={`/training/${courseId}/module/${nextModule.id}`}>
                <Button>
                  {t("training.nextModule") || "Next Module"}
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </Link>
            ) : (
              <Link href={`/training/${courseId}`}>
                <Button>
                  {t("training.finishCourse") || "Finish Course"}
                  <CheckCircle className="h-4 w-4 ml-2" />
                </Button>
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
