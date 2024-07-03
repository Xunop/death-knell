class Course:
    def __init__(self, year, semester, course_id, name, type, credit, gpa, normal_score, real_score, total_score, user_id):
        self.year = year
        self.semester = semester
        self.course_id = course_id
        self.name = name
        self.type = type
        self.credit = credit
        self.gpa = gpa
        self.normal_score = normal_score
        self.real_score = real_score
        self.total_score = total_score
        self.is_dead = self.check_if_dead(total_score)
        self.user_id = user_id

    @staticmethod
    def check_if_dead(total_score):
        """Determine if the course result is failing based on total_score."""
        if isinstance(total_score, int) and total_score < 60:
            return True
        elif total_score == '不及格':
            return True
        return False

    def __str__(self):
        base_info = f"{self.name} - Year: {self.year}, Semester: {self.semester}, Credit: {
            self.credit}, GPA: {self.gpa}, Total Score: {self.total_score}, Failed: {self.is_dead}"

        if self.normal_score not in [None, '', 'NULL']:
            base_info += f", Normal Score: {self.normal_score}"
        if self.real_score not in [None, '', 'NULL']:
            base_info += f", Real Score: {self.real_score}"

        return base_info

    def to_json(self):
        return {
            'year': self.year,
            'semester': self.semester,
            'course_id': self.course_id,
            'name': self.name,
            'type': self.type,
            'credit': self.credit,
            'gpa': self.gpa,
            'normal_score': self.normal_score,
            'real_score': self.real_score,
            'total_score': self.total_score,
            'is_dead': self.is_dead
        }

    def __eq__(self, other):
        return self.to_json() == other.to_json()
