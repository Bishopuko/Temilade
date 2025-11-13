<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Concerns\HasUuids;

class Template extends Model
{
    use HasFactory, HasUuids;

    /**
     * The attributes that are mass assignable.
     *
     * @var array
     */
    protected $fillable = [
        'template_code',
        'language',
        'subject',
        'body',
    ];

    /**
     * The attributes that should be cast.
     *
     * @var array
     */
    protected $casts = [
        'created_at' => 'datetime',
        'updated_at' => 'datetime',
    ];

    /**
     * Get the versions for the template.
     */
    public function versions()
    {
        return $this->hasMany(TemplateVersion::class)->orderBy('version_number', 'desc');
    }

    /**
     * Get the latest version of the template.
     */
    public function latestVersion()
    {
        return $this->hasOne(TemplateVersion::class)->latestOfMany('version_number');
    }

    /**
     * Get the current active version (latest version).
     */
    public function getCurrentVersionAttribute()
    {
        return $this->versions()->first();
    }
}
