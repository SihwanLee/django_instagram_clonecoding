from django.db import models
from django.utils import timezone
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin

class CustomUserManager(BaseUserManager):
	def create_user(self, email, password, name, username, date_of_birth, **kwargs):
		if not email:
			raise ValueError("Users must have an email address")
		if not password:
			raise ValueError("Users must have password")
		if not username:
			raise ValueError("Users must have a username")
		user = self.model(
			email = self.normalize_email(email),
			name = name,
			username = username,
			date_of_birth = date_of_birth,
			**kwargs
		)

		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password, name, username, date_of_birth):
		user = self.create_user(
			email = self.normalize_email(email),
			password = password,
			name = name,
			username = username,
			date_of_birth = date_of_birth,
		)
		user.is_superuser = True
		user.is_admin = True
		user.is_staff = True
		user.save(using=self._db)
		return user


class User(AbstractBaseUser, PermissionsMixin):
	objects = CustomUserManager()

	date_joined = models.DateTimeField(verbose_name="가입일",default=timezone.now, null=True)
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	is_admin = models.BooleanField(default=False)
	is_superuser = models.BooleanField(default=False)

	email = models.EmailField(verbose_name='이메일', max_length=50, null=False, unique=True)
	password = models.CharField(verbose_name="비밀번호", max_length=200)
	name = models.CharField(verbose_name="이름", max_length=50)
	username = models.CharField(verbose_name="닉네임", max_length=50, unique=True)
	date_of_birth = models.DateField(verbose_name="생년월일", max_length=8)
	profile_pic = models.ImageField(verbose_name="프로파일 사진", default="default_profile.png")

	USERNAME_FIELD='email'
	REQUIRED_FIELDS=['password', 'name', 'username', 'date_of_birth']

	# Relationships
	followers = models.ManyToManyField(
		'self',
		symmetrical=False,
		through='Relationship',
		related_name='followees',
		through_fields=('to_user', 'from_user')
		)

	@property
	def followers(self):
		follower_relationship = self.relationship_to_user.filter(relationship_type=Relationship.RELATIONSHIP_TYPE_FOLLOWING)
		follower_list = follower_relationship.values_list('from_user', flat=True)
		followers = User.objects.filter(pk__in=follower_list)
		return followers

	@property
	def followees(self):
		followee_relationship = self.relationship_from_user.filter(relationship_type=Relationship.RELATIONSHIP_TYPE_FOLLOWING)
		followee_list = followee_relationship.values_list('to_user', flat=True)
		followees = User.objects.filter(pk__in=followee_list)
		return followees

	@property
	def blocked(self):
		blocked_relationship = self.relationship_from_user.filter(relationship_type=Relationship.RELATIONSHIP_TYPE_BLOCKED)
		blocked_list = blocked_relationship.values_list('to_user', flat=True)
		blocked = User.objects.filter(pk__in=blocked_list)
		return blocked
		
	
	def follow(self, to_user):
		self.relationship_from_user.create(
			to_user = to_user,
			relationship_type='f'
			)
	
	def block(self, to_user):
		self.relationship_from_user.create(
			to_user=to_user,
			relationship_type='b'
			)

	def __str__(self):
		return self.email

	class Meta:
		db_table = "사용자 목록"
		verbose_name="사용자"
		verbose_name_plural="사용자"


class Relationship(models.Model):
    RELATIONSHIP_TYPE_FOLLOWING = 'f'
    RELATIONSHIP_TYPE_BLOCKED = 'b'
    CHOICE_TYPE = (
    	(RELATIONSHIP_TYPE_FOLLOWING, '팔로잉'),
    	(RELATIONSHIP_TYPE_BLOCKED, '차단'),
    	)
    from_user = models.ForeignKey(
    	User,
    	related_name='relationship_from_user',
    	on_delete=models.CASCADE,
    	)
    to_user = models.ForeignKey(
    	User,
    	related_name='relationship_to_user',
    	on_delete=models.CASCADE,
    	)
    relationship_type=models.CharField(max_length=1, choices=CHOICE_TYPE)

    def __str__(self):
    	return f"{self.from_user} follows {self.to_user}, type={self.relationship_type}"