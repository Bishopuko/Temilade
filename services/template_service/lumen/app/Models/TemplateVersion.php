<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Concerns\HasUuids;

class TemplateVersion extends Model
{
    use HasFactory, HasUuids;

    /**
     * The attributes that are mass assignable.
     *
     * @var array
     */
    protected $fillable = [
        'template_id',
        'version_number',
        'body',
        'subject',
        'variables',
    ];

    /**
     * The attributes that should be cast.
     *
     * @var array
     */
    protected $casts = [
        'variables' => 'array',
        'created_at' => 'datetime',
        'updated_at' => 'datetime',
    ];

    /**
     * Get the template that owns the version.
     */
    public function template()
    {
        return $this->belongsTo(Template::class);
    }

    /**
     * Render the template with variable substitution.
     *
     * @param array $data
     * @return array
     */
    public function render(array $data = [])
    {
        $rendered = [
            'subject' => $this->subject,
            'body' => $this->body,
        ];

        foreach ($data as $key => $value) {
            $placeholder = '{{' . $key . '}}';
            $rendered['subject'] = str_replace($placeholder, $value, $rendered['subject']);
            $rendered['body'] = str_replace($placeholder, $value, $rendered['body']);
        }

        return $rendered;
    }
}
