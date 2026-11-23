import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { taxonomyService } from '../../services/taxonomyService';
import { complaintService } from '../../services/complaintService';
import { uploadService } from '../../services/uploadService';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Textarea } from '../../components/ui/Textarea';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import { Notification } from '../../components/ui/Notification';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import type { TaxonomyHierarchyResponse, StudentComplaintCreatePayload } from '../../types';
import {
  Send,
  Upload,
  CheckCircle2,
  AlertCircle,
  FileText,
  Calendar,
  Clock,
  MapPin,
  Phone,
  Image as ImageIcon,
  Check,
} from 'lucide-react';

export const RaiseQueryPage: React.FC = () => {
  const navigate = useNavigate();

  // Taxonomy hierarchy state
  const [taxonomy, setTaxonomy] = useState<TaxonomyHierarchyResponse | null>(null);
  const [loadingTaxonomy, setLoadingTaxonomy] = useState<boolean>(true);

  // Form states
  const [messageType, setMessageType] = useState<string>('Grievance');
  const [category, setCategory] = useState<string>('');
  const [subCategory, setSubCategory] = useState<string>('');
  const [specificCategories, setSpecificCategories] = useState<string[]>([]);
  const [building, setBuilding] = useState<string>('');
  const [subBlock, setSubBlock] = useState<string>('');
  const [roomType, setRoomType] = useState<string>('Room No');
  const [roomNumber, setRoomNumber] = useState<string>('');
  const [specifiedLocation, setSpecifiedLocation] = useState<string>('');
  const [contactNumber, setContactNumber] = useState<string>('');
  const [availabilityDate, setAvailabilityDate] = useState<string>(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  });
  const [timeSlot, setTimeSlot] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [declaration1, setDeclaration1] = useState<boolean>(false);
  const [declaration2, setDeclaration2] = useState<boolean>(false);
  const [declaration3, setDeclaration3] = useState<boolean>(false);

  // Attachment states
  const [uploadingPhoto, setUploadingPhoto] = useState<boolean>(false);
  const [uploadedPhotoName, setUploadedPhotoName] = useState<string | null>(null);
  const [uploadedPhotoFilename, setUploadedPhotoFilename] = useState<string | null>(null);
  const [uploadedPhotoSha256, setUploadedPhotoSha256] = useState<string | null>(null);

  // Submission status
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successResult, setSuccessResult] = useState<{ token: string; message: string } | null>(null);

  // Fetch taxonomy on mount
  useEffect(() => {
    const fetchTaxonomy = async () => {
      try {
        const data = await taxonomyService.getHierarchy();
        setTaxonomy(data);
        if (data.maintenance_categories?.length > 0) {
          setCategory(data.maintenance_categories[0]);
        }
        if (data.campus_blocks?.length > 0) {
          setBuilding(data.campus_blocks[0]);
        }
        if (data.time_slots?.length > 0) {
          setTimeSlot(data.time_slots[0]);
        }
      } catch (err: any) {
        setErrorMsg('Failed to load facility categories. Check backend connectivity.');
      } finally {
        setLoadingTaxonomy(false);
      }
    };
    fetchTaxonomy();
  }, []);

  // Cascading Category -> SubCategory reset
  const availableSubCategories = React.useMemo(() => {
    if (!taxonomy || !category) return [];
    const catMap = taxonomy.hierarchy?.[category];
    return catMap ? Object.keys(catMap) : [];
  }, [taxonomy, category]);

  useEffect(() => {
    if (availableSubCategories.length > 0) {
      setSubCategory(availableSubCategories[0]);
    } else {
      setSubCategory('');
    }
    setSpecificCategories([]);
  }, [category, availableSubCategories]);

  // Cascading SubCategory -> Specific Categories reset
  const availableSpecificCategories: string[] = React.useMemo(() => {
    if (!taxonomy || !category || !subCategory) return [];
    const val: any = taxonomy.hierarchy?.[category]?.[subCategory];
    if (!val) return [];
    if (Array.isArray(val)) return val;
    if (typeof val === 'object') return Object.keys(val);
    return [];
  }, [taxonomy, category, subCategory]);

  useEffect(() => {
    setSpecificCategories([]);
  }, [subCategory]);

  const toggleSpecificCategory = (item: string) => {
    setSpecificCategories((prev) =>
      prev.includes(item) ? prev.filter((x) => x !== item) : [...prev, item]
    );
  };

  // Photo upload handler
  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingPhoto(true);
    setErrorMsg(null);
    try {
      const res = await uploadService.uploadPhoto(file);
      setUploadedPhotoName(file.name);
      setUploadedPhotoFilename(res.stored_filename);
      setUploadedPhotoSha256(res.sha256);
    } catch (err: any) {
      setErrorMsg(err.message || 'Photo upload validation failed.');
    } finally {
      setUploadingPhoto(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!declaration1 || !declaration2 || !declaration3) {
      setErrorMsg('All 3 mandatory declarations must be accepted before submitting your query.');
      return;
    }

    if (description.trim().length < 5) {
      setErrorMsg('Description must be at least 5 characters in length.');
      return;
    }

    if (contactNumber.replace(/\D/g, '').length < 10) {
      setErrorMsg('Please provide a valid 10-digit mobile contact number.');
      return;
    }

    const payload: StudentComplaintCreatePayload = {
      category_type: 'Maintenance / Electrical Complaints',
      message_type: messageType,
      category,
      sub_category: subCategory || undefined,
      specific_categories: specificCategories,
      building,
      sub_block: subBlock || undefined,
      room_type: roomType,
      room_number: roomType === 'Room No' ? roomNumber : undefined,
      specified_location: roomType !== 'Room No' ? specifiedLocation : undefined,
      contact_number: contactNumber,
      availability_date: availabilityDate,
      time_slot: timeSlot,
      description: description.trim(),
      declarations_accepted: true,
      photo_stored_filename: uploadedPhotoFilename || undefined,
      photo_sha256: uploadedPhotoSha256 || undefined,
    };

    setSubmitting(true);
    try {
      const result = await complaintService.submitStudentComplaint(payload);
      setSuccessResult({
        token: result.token,
        message: result.message,
      });
    } catch (err: any) {
      setErrorMsg(err.message || 'Unable to register complaint. Please check your entries.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loadingTaxonomy) {
    return <LoadingSpinner label="Loading campus facility taxonomy..." className="py-20" />;
  }

  if (successResult) {
    return (
      <Card className="max-w-2xl mx-auto shadow-md border-emerald-200">
        <CardContent className="p-8 text-center space-y-5">
          <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-9 h-9" />
          </div>
          <div className="space-y-1">
            <h2 className="text-xl font-bold text-[#172D28]">Complaint Registered Successfully</h2>
            <p className="text-xs text-[#52605B]">Your facility request has been recorded into the live campus ledger.</p>
          </div>

          <div className="p-5 rounded-xl bg-[#F5F7F2] border border-[#DCE5D8] max-w-sm mx-auto">
            <span className="text-[11px] font-semibold text-[#52605B] uppercase tracking-wider block">
              Complaint Token
            </span>
            <span className="text-2xl font-mono font-bold text-[#203A32] mt-1 block">
              {successResult.token}
            </span>
          </div>

          <p className="text-xs text-[#52605B] max-w-md mx-auto leading-relaxed">
            Your request has been routed to the relevant facility squad and scheduled for physical inspection during your preferred time window.
          </p>

          <div className="flex justify-center gap-3 pt-3">
            <Button
              variant="outline"
              onClick={() => {
                setSuccessResult(null);
                setDescription('');
                setSpecificCategories([]);
                setUploadedPhotoFilename(null);
                setUploadedPhotoName(null);
              }}
            >
              Raise Another Query
            </Button>
            <Button variant="primary" onClick={() => navigate('/student/history')}>
              View in History
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#172D28] tracking-tight">Raise a Facility Query</h1>
        <p className="text-xs text-[#52605B] mt-1">
          Submit a campus maintenance request. All requests undergo automatic severity assessment and priority queueing.
        </p>
      </div>

      {errorMsg && <Notification type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 1. Categorisation Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <FileText className="w-4 h-4 text-[#203A32]" /> 1. Issue Classification
            </CardTitle>
            <CardDescription>LPU RMS 19-Category Hierarchical Classification</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Select
                label="Message Type"
                value={messageType}
                onChange={(e) => setMessageType(e.target.value)}
                options={taxonomy?.message_types.map((m) => ({ value: m, label: m }))}
                required
              />

              <Select
                label="Primary Category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                options={taxonomy?.maintenance_categories.map((c) => ({ value: c, label: c }))}
                required
              />
            </div>

            {availableSubCategories.length > 0 && (
              <Select
                label="Subcategory"
                value={subCategory}
                onChange={(e) => setSubCategory(e.target.value)}
                options={availableSubCategories.map((s) => ({ value: s, label: s }))}
                required
              />
            )}

            {availableSpecificCategories.length > 0 && (
              <div className="space-y-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#172D28]">
                  Specific Issue Options (Check all that apply)
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 p-3 rounded-lg border border-[#DCE5D8] bg-[#F5F7F2]/40 max-h-48 overflow-y-auto">
                  {availableSpecificCategories.map((item) => (
                    <label
                      key={item}
                      className="flex items-center gap-2 text-xs text-[#172D28] cursor-pointer hover:text-[#203A32]"
                    >
                      <input
                        type="checkbox"
                        checked={specificCategories.includes(item)}
                        onChange={() => toggleSpecificCategory(item)}
                        className="rounded border-[#A8B9A3] text-[#203A32] focus:ring-[#203A32]"
                      />
                      <span>{item}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 2. Location & Contact Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <MapPin className="w-4 h-4 text-[#203A32]" /> 2. Location & Contact
            </CardTitle>
            <CardDescription>Specify precise campus coordinates for dispatch crews</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Select
                label="Campus Building / Block"
                value={building}
                onChange={(e) => setBuilding(e.target.value)}
                options={taxonomy?.campus_blocks.map((b) => ({ value: b, label: b }))}
                required
              />

              <Select
                label="Sub Block / Wing"
                value={subBlock}
                onChange={(e) => setSubBlock(e.target.value)}
                options={[
                  { value: '', label: 'None / General' },
                  ...(taxonomy?.campus_sub_blocks.map((s) => ({ value: s, label: `Sub Block ${s}` })) || []),
                ]}
              />

              <Select
                label="Location Type"
                value={roomType}
                onChange={(e) => setRoomType(e.target.value)}
                options={[
                  { value: 'Room No', label: 'Room Number' },
                  { value: 'Any Other', label: 'Common Area / Other' },
                ]}
                required
              />
            </div>

            {roomType === 'Room No' ? (
              <Input
                label="Room Number"
                placeholder="e.g. 204 or Ground Floor Lab"
                value={roomNumber}
                onChange={(e) => setRoomNumber(e.target.value)}
                required
              />
            ) : (
              <Input
                label="Specific Location Details"
                placeholder="e.g. 3rd Floor East Washroom near Staircase B"
                value={specifiedLocation}
                onChange={(e) => setSpecifiedLocation(e.target.value)}
                required
              />
            )}

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <Input
                label="Contact Number"
                placeholder="10-digit mobile number"
                value={contactNumber}
                onChange={(e) => setContactNumber(e.target.value)}
                leftIcon={<Phone className="w-4 h-4" />}
                required
              />

              <Input
                label="Inspection Date"
                type="date"
                value={availabilityDate}
                onChange={(e) => setAvailabilityDate(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                leftIcon={<Calendar className="w-4 h-4" />}
                required
              />

              <Select
                label="Preferred Time Window"
                value={timeSlot}
                onChange={(e) => setTimeSlot(e.target.value)}
                options={taxonomy?.time_slots.map((t) => ({ value: t, label: t }))}
                required
              />
            </div>
          </CardContent>
        </Card>

        {/* 3. Description & Photo Attachment */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <FileText className="w-4 h-4 text-[#203A32]" /> 3. Problem Description & Evidence
            </CardTitle>
            <CardDescription>Detailed issue breakdown for engineering triage</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              label="Detailed Problem Description"
              placeholder="Describe the issue clearly (e.g. electrical sparking, leaking tap, broken fixture)..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={500}
              showCount
              rows={4}
              required
            />

            {/* Photo Attachment */}
            <div className="p-4 rounded-xl border border-dashed border-[#DCE5D8] bg-[#F5F7F2]/40 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-[#172D28] flex items-center gap-1.5">
                  <ImageIcon className="w-4 h-4 text-[#A8B9A3]" /> Optional Photo Attachment
                </span>
                <span className="text-[10px] text-[#52605B]">Max 10MB • PNG, JPEG, WebP</span>
              </div>

              {uploadedPhotoName ? (
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs">
                  <span className="flex items-center gap-1.5 font-medium">
                    <Check className="w-4 h-4 text-emerald-600" /> {uploadedPhotoName}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      setUploadedPhotoName(null);
                      setUploadedPhotoFilename(null);
                      setUploadedPhotoSha256(null);
                    }}
                    className="text-xs font-medium text-emerald-800 hover:text-emerald-950 underline"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <label className="flex flex-col items-center justify-center p-3 rounded-lg border border-[#DCE5D8] bg-white hover:border-[#203A32] cursor-pointer transition-colors text-center">
                  <Upload className="w-5 h-5 text-[#A8B9A3] mb-1" />
                  <span className="text-xs font-medium text-[#172D28]">
                    {uploadingPhoto ? 'Validating and uploading...' : 'Click to attach damage photo'}
                  </span>
                  <input
                    type="file"
                    accept="image/png, image/jpeg, image/webp"
                    className="hidden"
                    onChange={handlePhotoUpload}
                    disabled={uploadingPhoto}
                  />
                </label>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 4. Mandatory Declarations Card */}
        <Card className="border-[#DCE5D8] bg-[#F5F7F2]/50">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#203A32]" /> 4. Mandatory Student Declarations
            </CardTitle>
            <CardDescription>Must confirm all declarations before registering ticket</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <label className="flex items-start gap-3 text-xs text-[#172D28] cursor-pointer">
              <input
                type="checkbox"
                checked={declaration1}
                onChange={(e) => setDeclaration1(e.target.checked)}
                className="mt-0.5 rounded border-[#A8B9A3] text-[#203A32] focus:ring-[#203A32]"
              />
              <span>I confirm that the location and room specified above are accurate and accessible during the selected time window.</span>
            </label>

            <label className="flex items-start gap-3 text-xs text-[#172D28] cursor-pointer">
              <input
                type="checkbox"
                checked={declaration2}
                onChange={(e) => setDeclaration2(e.target.checked)}
                className="mt-0.5 rounded border-[#A8B9A3] text-[#203A32] focus:ring-[#203A32]"
              />
              <span>I have checked the self-help FAQ guidelines and verified that physical technician intervention is required.</span>
            </label>

            <label className="flex items-start gap-3 text-xs text-[#172D28] cursor-pointer">
              <input
                type="checkbox"
                checked={declaration3}
                onChange={(e) => setDeclaration3(e.target.checked)}
                className="mt-0.5 rounded border-[#A8B9A3] text-[#203A32] focus:ring-[#203A32]"
              />
              <span>I consent to maintenance personnel entering the specified premises to inspect and remediate the reported defect.</span>
            </label>
          </CardContent>
        </Card>

        {/* Submit Action */}
        <div className="flex justify-end gap-3 pt-2">
          <Button
            type="submit"
            variant="primary"
            size="lg"
            isLoading={submitting}
            leftIcon={<Send className="w-4 h-4" />}
          >
            Submit Facility Query
          </Button>
        </div>
      </form>
    </div>
  );
};
