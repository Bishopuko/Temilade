<?php

namespace App\Http\Controllers;

use App\Models\Template;
use App\Models\TemplateVersion;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Validator;
use Illuminate\Validation\Rule;

class TemplateController extends Controller
{
    /**
     * Display a listing of templates.
     *
     * @return \Illuminate\Http\JsonResponse
     */
    public function index(Request $request)
    {
        $language = $request->query('language', 'en');
        $perPage = $request->query('per_page', 15);

        $templates = Template::where('language', $language)
            ->with('latestVersion')
            ->paginate($perPage);

        return response()->json($templates);
    }

    /**
     * Store a newly created template.
     *
     * @param  \Illuminate\Http\Request  $request
     * @return \Illuminate\Http\JsonResponse
     */
    public function store(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'template_code' => 'required|string|unique:templates|max:255',
            'language' => 'required|string|max:10',
            'subject' => 'nullable|string|max:255',
            'body' => 'required|string',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'error' => 'Validation failed',
                'messages' => $validator->errors()
            ], 422);
        }

        try {
            $template = Template::create($request->only(['template_code', 'language', 'subject', 'body']));

            // Create initial version
            $version = TemplateVersion::create([
                'template_id' => $template->id,
                'version_number' => 1,
                'body' => $request->body,
                'subject' => $request->subject,
                'variables' => $this->extractVariables($request->body, $request->subject),
            ]);

            // Clear cache
            Cache::forget("template:{$template->template_code}:{$template->language}");

            return response()->json([
                'message' => 'Template created successfully',
                'template' => $template->load('latestVersion'),
            ], 201);

        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Failed to create template',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Display the specified template.
     *
     * @param  string  $templateCode
     * @return \Illuminate\Http\JsonResponse
     */
    public function show(Request $request, $templateCode)
    {
        $language = $request->query('language', 'en');

        $template = Template::where('template_code', $templateCode)
            ->where('language', $language)
            ->with('versions')
            ->first();

        if (!$template) {
            return response()->json(['error' => 'Template not found'], 404);
        }

        return response()->json($template);
    }

    /**
     * Update the specified template.
     *
     * @param  \Illuminate\Http\Request  $request
     * @param  string  $templateCode
     * @return \Illuminate\Http\JsonResponse
     */
    public function update(Request $request, $templateCode)
    {
        $language = $request->query('language', 'en');

        $template = Template::where('template_code', $templateCode)
            ->where('language', $language)
            ->first();

        if (!$template) {
            return response()->json(['error' => 'Template not found'], 404);
        }

        $validator = Validator::make($request->all(), [
            'subject' => 'nullable|string|max:255',
            'body' => 'required|string',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'error' => 'Validation failed',
                'messages' => $validator->errors()
            ], 422);
        }

        try {
            $template->update($request->only(['subject', 'body']));

            // Create new version
            $latestVersion = $template->versions()->max('version_number') ?? 0;
            $version = TemplateVersion::create([
                'template_id' => $template->id,
                'version_number' => $latestVersion + 1,
                'body' => $request->body,
                'subject' => $request->subject,
                'variables' => $this->extractVariables($request->body, $request->subject),
            ]);

            // Clear cache
            Cache::forget("template:{$template->template_code}:{$template->language}");

            return response()->json([
                'message' => 'Template updated successfully',
                'template' => $template->load('latestVersion'),
            ]);

        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Failed to update template',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Remove the specified template.
     *
     * @param  string  $templateCode
     * @return \Illuminate\Http\JsonResponse
     */
    public function destroy(Request $request, $templateCode)
    {
        $language = $request->query('language', 'en');

        $template = Template::where('template_code', $templateCode)
            ->where('language', $language)
            ->first();

        if (!$template) {
            return response()->json(['error' => 'Template not found'], 404);
        }

        try {
            // Clear cache
            Cache::forget("template:{$template->template_code}:{$template->language}");

            $template->delete();

            return response()->json(['message' => 'Template deleted successfully']);

        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Failed to delete template',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Render a template with provided data.
     *
     * @param  \Illuminate\Http\Request  $request
     * @param  string  $templateCode
     * @return \Illuminate\Http\JsonResponse
     */
    public function render(Request $request, $templateCode)
    {
        $language = $request->query('language', 'en');
        $data = $request->input('data', []);

        // Check cache first
        $cacheKey = "template:{$templateCode}:{$language}";
        $template = Cache::remember($cacheKey, 3600, function () use ($templateCode, $language) {
            return Template::where('template_code', $templateCode)
                ->where('language', $language)
                ->with('latestVersion')
                ->first();
        });

        if (!$template || !$template->latestVersion) {
            return response()->json(['error' => 'Template not found'], 404);
        }

        try {
            $rendered = $template->latestVersion->render($data);

            return response()->json([
                'template_code' => $template->template_code,
                'language' => $template->language,
                'rendered' => $rendered,
            ]);

        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Failed to render template',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Extract variables from template content.
     *
     * @param  string  $body
     * @param  string|null  $subject
     * @return array
     */
    private function extractVariables($body, $subject = null)
    {
        $variables = [];
        $content = $body . ' ' . ($subject ?? '');

        preg_match_all('/\{\{(\w+)\}\}/', $content, $matches);

        if (!empty($matches[1])) {
            $variables = array_unique($matches[1]);
        }

        return $variables;
    }
}
