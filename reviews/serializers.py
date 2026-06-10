from rest_framework import serializers
from .models import Review


class ReviewReplySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'username', 'comment', 'created_at']

    def get_created_at(self, obj):
        return obj.created_at.strftime('%d %b %Y, %H:%M')


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    created_at = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    can_reply = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id',
            'username',
            'rating',
            'comment',
            'parent',
            'approved',
            'created_at',
            'replies',
            'can_edit',
            'can_delete',
            'can_reply'
        ]
        read_only_fields = [
            'id',
            'username',
            'approved',
            'created_at',
            'replies',
            'can_edit',
            'can_delete',
            'can_reply'
        ]
    def get_created_at(self, obj):
        luni = {
            1: 'ianuarie', 2: 'februarie', 3: 'martie',
            4: 'aprilie', 5: 'mai', 6: 'iunie',
            7: 'iulie', 8: 'august', 9: 'septembrie',
            10: 'octombrie', 11: 'noiembrie', 12: 'decembrie'
        }
        luna = luni[obj.created_at.month]
        return f"{obj.created_at.day} {luna} {obj.created_at.year}, {obj.created_at.strftime('%H:%M')}"

    def get_replies(self, obj):
        replies = obj.replies.filter(
            approved=True
        ).select_related('user').order_by('created_at')

        return ReviewReplySerializer(replies, many=True).data

    def get_can_edit(self, obj):
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            return False

        return obj.user == request.user and obj.parent is None

    def get_can_delete(self, obj):
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            return False

        return obj.user == request.user and obj.parent is None

    def get_can_reply(self, obj):
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            return False

        return request.user.is_staff and obj.parent is None