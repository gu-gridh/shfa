from tabnanny import verbose
import diana.abstract.models as abstract
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models
import apps.geography.models as geography
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

# Validators
raa_validator = RegexValidator(r"([A-Za-z]+)( )(\d+:?\d+?)")
lamning_validator = RegexValidator(r"(L\d+)(:)(\d+)")

############ TAGS #####################
class CarvingTag(abstract.AbstractTagModel):
    # A tag model, of which a site can have many
    # tags, and tags can be used on many sites
    # Observe: Simple listing of occurences, not enumeration of all figures
    pass

    legacy_id = models.PositiveBigIntegerField(null=True, blank=True, verbose_name=_("legacy id"))


    class Meta:
        verbose_name = _("Type of carving")
        verbose_name_plural = _("Types of carving")

    def __str__(self) -> str:
        return self.text
    
    def __repr__(self) -> str:
        return str(self)

class KeywordTag(abstract.AbstractTagModel):
    # Keywords relating to the image
    pass

    legacy_id = models.PositiveBigIntegerField(null=True, blank=True, verbose_name=_("legacy id"))


    class Meta:
        verbose_name = _("Image keyword")
        verbose_name_plural = _("Image keywords")

    def __str__(self) -> str:
        return self.text
    
    def __repr__(self) -> str:
        return str(self)


class DatingTag(abstract.AbstractTagModel):
    # A tag model, of which a site can have many
    # tags, and tags can be used on many sites
    # Motivation: Sites can contain figures with different dating
    
    legacy_id = models.PositiveBigIntegerField(null=True, blank=True, verbose_name=_("legacy id"))
    abbreviation = models.CharField(max_length=32, verbose_name=_("Abbreviation"), help_text=_("Common abbreviation of the dating estimation."))
    certainty = models.CharField(max_length=64, null=True, blank=True, verbose_name=_("Certainty of dating"), help_text=_("A free-form description of the certainty of the dating."))

    class Meta:
        verbose_name = _("Dating")
        verbose_name_plural = _("Datings")

    def __str__(self) -> str:
        return self.text
    
    def __repr__(self) -> str:
        return str(self)


class ImageTypeTag(abstract.AbstractTagModel):
    
    legacy_id = models.PositiveBigIntegerField(null=True, blank=True, verbose_name=_("legacy id"))


    class Meta:
        verbose_name = _("Type of image")
        verbose_name_plural = _("Types of image")

    def __str__(self) -> str:
        return self.text
    
    def __repr__(self) -> str:
        return str(self)

####################################

class Collection(abstract.AbstractBaseModel):

    name = models.CharField(max_length=128, unique=True, verbose_name=_("name"), help_text=_("Name of the collection"))
    legacy_id = models.PositiveBigIntegerField(null=True, blank=True, verbose_name=_("legacy id"))


    class Meta:
        verbose_name = _("Collection")
        verbose_name_plural = _("Collections")

    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return str(self)

class Author(abstract.AbstractBaseModel):
    # A photographer, or owner, 
    # can be a person or institution

    name = models.CharField(max_length=256, unique=True, verbose_name=_("name"), help_text=_("Free-form name of the creator, photographer or author."))
    legacy_id = models.PositiveBigIntegerField(null=True, blank=True, verbose_name=_("legacy id"))


    class Meta:
        verbose_name = _("Creator")
        verbose_name_plural = _("Creators")

    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return str(self)


class Institution(abstract.AbstractBaseModel):

    legacy_id = models.PositiveBigIntegerField(null=True, blank=True, verbose_name=_("legacy id"))

    name    = models.CharField(max_length=512, unique=True, verbose_name=_("name"), help_text=_("Name of the institution"))
    address = models.TextField(null=True, blank=True, verbose_name=_("address"), help_text=_("Physical address details, if applicable."))
    url     = models.URLField(max_length=512, null=True, blank=True, verbose_name=_("url"), help_text=_("URL or website address to the institution, if applicable."))
    email   = models.EmailField(max_length=512, null=True, blank=True, verbose_name=_("email"), help_text=_("E-mail address of the institution, if applicable."))

    class Meta:
        verbose_name = _("Institution")
        verbose_name_plural = _("Institutions")

    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return str(self)


########## Image material ##############
class RockCarvingObject(abstract.AbstractBaseModel):

    name = models.CharField(max_length=128, unique=True, verbose_name=_("name"), help_text=_("Ad-hoc naming of the rock carving object/motif."))
    code = models.CharField(max_length=128, null=True, blank=True, verbose_name=_("code"), help_text=_("Standardized code of the object, if applicable."))


    # TODO: Site?

    class Meta:
        verbose_name = _("Rock carving object")
        verbose_name_plural = _("Rock carving objects")

    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return str(self)


class Site(abstract.AbstractBaseModel):
    # Represents the archaeological sites of interests
    # containing carvings or other remnants

    # Various IDs
    ksamsok_id      = models.CharField(max_length=128, unique=True, null=True, blank=True, verbose_name=_("Fornsök ID"), help_text=_("UUID at the Fornsök (SOCH) portal.")) 
    raa_id          = models.CharField(max_length=128, unique=False, null=True, blank=True, verbose_name=_("RAÄ ID"), help_text=_("Deprecated ID for heritage remains."), validators=[raa_validator])
    lamning_id      = models.CharField(max_length=128, unique=True, null=True, blank=True, verbose_name=_("shfa.lamning_id"), help_text=_("Current ID for heritage remains."), validators=[lamning_validator])
    askeladden_id   = models.CharField(max_length=256, unique=True, null=True, blank=True, verbose_name=_("shfa.askeladden_id"), help_text=_("ID at the Norwegian Askeladden database, if applicable."))
    lokalitet_id    = models.CharField(max_length=128, unique=True, null=True, blank=True, verbose_name=_("shfa.lokalitet_id"), help_text=_("ID at the Danish <i>lokalitet</i> database, if applicable."))

    # Location
    coordinates  = models.PointField(null=True, blank=True, verbose_name=_("Coordinates"), help_text=_("Mid-point coordinates of the site."))
    municipality = models.ForeignKey(geography.LocalAdministrativeUnit, null=True, blank=True,  related_name="sites", on_delete=models.SET_NULL, verbose_name=_("Municipality"), help_text=_("Municipality, or international local administrative unit where the site is located."))
    parish       = models.ForeignKey(geography.Parish, null=True, blank=True,  related_name="sites", on_delete=models.SET_NULL, verbose_name=_("Parish"), help_text=_("Swedish ecclesiastical administrative unit where the site is located."))
    province     = models.ForeignKey(geography.Province, null=True, blank=True,  related_name="sites", on_delete=models.SET_NULL, verbose_name=_("Province"), help_text=_("Swedish traditional subdivision of territory where the site is located."))

    # Placename is particularly used outside of Sweden
    placename       = models.CharField(max_length=256, null=True, blank=True, verbose_name=_("Placename"), help_text=_("Free-form, non-indexed placename of the site."))

    def __str__(self) -> str:


        if self.raa_id:
            name_str =  f"{self.raa_id}"
        elif self.lamning_id:
            name_str =  f"{self.lamning_id}"
        elif self.askeladden_id:
            name_str = f"Askeladden {self.askeladden_id}"
        elif self.lokalitet_id:
            name_str = f"Lokalitet {self.askeladden_id}"
        else:
            name_str = ""

        return name_str
    
    class Meta:
        verbose_name = _("Site")
        verbose_name_plural = _("Sites")


class Image(abstract.AbstractTIFFImageModel):

    # Rock carving site
    legacy_id = models.PositiveBigIntegerField(null=True, blank=True, verbose_name=_("legacy id"))

    site        = models.ForeignKey(Site, null=True, blank=True, on_delete=models.PROTECT, verbose_name=_("Site"), help_text=_("Rock carving site"))
    
    # Metadata on collections
    collection  = models.ForeignKey(Collection, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_("Collection"), help_text=_("Collection from which the image originates."))
    author      = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Image creator"), help_text=_("Creator, photographer or author of the original image."))
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Institution"), help_text=_("Original institution housing the image."))
    reference   = models.CharField(max_length=512, null=True, blank=True, verbose_name=_("References"), help_text=_("Reference notes on the image."))
    
    # Date stamps
    year        = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Creation year"), help_text=_("Original creation date of the image."))
    date_note   = models.TextField(null=True, blank=True, verbose_name=_("Note on date"), help_text=_("Free-form note on the certainty or context of the dating."))

    # Motif rock carving object
    rock_carving_object = models.ForeignKey(RockCarvingObject, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Rock carving object"), help_text=_("Rock carving object in the image."))
    
    # Tags
    keywords = models.ManyToManyField(KeywordTag, blank=True, related_name="images", verbose_name=_("Keywords"), help_text=_("Keywords in the image, used for categorization."))
    type     = models.ForeignKey(ImageTypeTag, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_("Type"), help_text=_("Type of image medium, material or origin."))    
    carving_tags    = models.ManyToManyField(CarvingTag, blank=True, related_name="images", verbose_name=_("Carvings in image"), help_text=_("A list of rock carving motifs in the image."))
    dating_tags     = models.ManyToManyField(DatingTag, blank=True, related_name="images", verbose_name=_("Datings"), help_text=_("A list of dating estimations occurring in the image."))
    
    class Meta:
        verbose_name = _("Image")
        verbose_name_plural = _("Images")

    def __str__(self) -> str:
        return f"Image {self.file.name} of {self.site}"
    
    def __repr__(self) -> str:
        return str(self)


class Compilation(abstract.AbstractBaseModel):

    # A manual compilation of images, could be used for display
    # of certain collages, for example

    name = models.CharField(max_length=128, unique=True)
    images = models.ManyToManyField(Image, blank=True, related_name="compilations", verbose_name="Images in compilation", help_text=_("List of images to group together."))

    class Meta:
        verbose_name = _("Compilation")
        verbose_name_plural = _("Compilations")

    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return str(self)
