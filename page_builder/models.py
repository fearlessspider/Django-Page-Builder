from django.db import models
from django.urls import reverse, resolve
from django.utils.timesince import timesince
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now


class Page(models.Model):
    STATUS_DRAFT = 1
    STATUS_PUBLISHED = 2
    STATUS_CHOICES = (
        (STATUS_DRAFT, _("Draft")),
        (STATUS_PUBLISHED, _("Published")),
    )

    created = models.DateTimeField(null=True, editable=False)
    updated = models.DateTimeField(null=True, editable=False)
    parent = models.ForeignKey("Page", on_delete=models.CASCADE,
                               blank=True, null=True, related_name="children")
    in_menu = models.BooleanField(_("Show in menu"), default=True)
    title = models.CharField(max_length=255)
    slug = models.CharField(_("URL"), max_length=255, blank=True,
                            help_text=_("Leave blank to have the URL auto-generated from "
                                        "the title."))
    login_required = models.BooleanField(_("Login required"), default=False,
                                         help_text=_("If checked, only logged in users can view this page"))
    status = models.IntegerField(_("Status"),
                                 choices=STATUS_CHOICES, default=STATUS_PUBLISHED,
                                 help_text=_("With Draft chosen, will only be shown for admin users "
                                             "on the site."))
    publish_date = models.DateTimeField(_("Published from"),
                                        help_text=_("With Published chosen, won't be shown until this time"),
                                        blank=True, null=True, db_index=True)
    expiry_date = models.DateTimeField(_("Expires on"),
                                       help_text=_("With Published chosen, won't be shown after this time"),
                                       blank=True, null=True)

    class Meta:
        verbose_name = _("Page")
        verbose_name_plural = _("Pages")
        ordering = ("title",)
        #order_with_respect_to = "parent"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        _now = now()
        self.updated = _now
        if not self.id:
            self.created = _now
        if self.publish_date is None:
            self.publish_date = now()
        super(Page, self).save(*args, **kwargs)

    def publish_date_since(self):
        return timesince(self.publish_date)

    publish_date_since.short_description = _("Published from")

    def published(self):
        """
        For non-staff users, return True when status is published and
        the publish and expiry dates fall before and after the
        current date when specified.
        """
        return (self.status == self.STATUS_PUBLISHED and
                (self.publish_date is None or self.publish_date <= now()) and
                (self.expiry_date is None or self.expiry_date >= now()))

    def get_absolute_url(self):
        slug = self.slug
        if slug == "/":
            return reverse("home")
        else:
            return reverse("page", kwargs={"slug": slug})

    def get_slug(self):
        """
        Recursively build the slug from the chain of parents.
        """
        if self.parent is not None:
            return "%s/%s" % (self.parent.slug, self.slug)
        return self.slug

    def set_slug(self, new_slug):
        """
        Changes this page's slug, and all other pages whose slugs
        start with this page's slug.
        """
        slug_prefix = "%s/" % self.slug
        for page in Page.objects.filter(slug__startswith=slug_prefix):
            if not page.overridden():
                page.slug = new_slug + page.slug[len(self.slug):]
                page.save()
        self.slug = new_slug
        self.save()

    def set_parent(self, new_parent):
        """
        Change the parent of this page, changing this page's slug to match
        the new parent if necessary.
        """
        self_slug = self.slug
        old_parent_slug = self.parent.slug if self.parent else ""
        new_parent_slug = new_parent.slug if new_parent else ""

        # Make sure setting the new parent won't cause a cycle.
        parent = new_parent
        while parent is not None:
            if parent.pk == self.pk:
                raise AttributeError("You can't set a page or its child as"
                                     " a parent.")
            parent = parent.parent

        self.parent = new_parent
        self.save()

        if self_slug:
            if not old_parent_slug:
                self.set_slug("/".join((new_parent_slug, self.slug)))
            elif self.slug.startswith(old_parent_slug):
                new_slug = self.slug.replace(old_parent_slug,
                                             new_parent_slug, 1)
                self.set_slug(new_slug.strip("/"))

    def overridden(self):
        """
        Returns ``True`` if the page's slug has an explicitly defined
        urlpattern and is therefore considered to be overridden.
        """
        from page_builder.views import PageView
        page_url = reverse("page", kwargs={"slug": self.slug})
        resolved_view = resolve(page_url)[0]
        return resolved_view != PageView

